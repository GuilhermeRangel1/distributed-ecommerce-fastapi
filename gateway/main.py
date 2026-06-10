import asyncio
import httpx
import logging
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import HTMLResponse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(title="API Gateway")

SERVICES = {
    "users": "https://users:5001",
    "products": "https://products-replica-a:5002",
    "orders": "https://orders:5003"
}

PRODUCTS_REPLICAS = [
    "https://products-replica-a:5002",
    "https://products-replica-b:5012"
]
current_replica_index = 0

services_health = {status: "unknown" for status in SERVICES}
previous_health = {status: "unknown" for status in SERVICES}

async def heartbeat_checker():
    async with httpx.AsyncClient(verify=False) as client:
        while True:
            for service_name, base_url in SERVICES.items():
                try:
                    response = await client.get(f"{base_url}/health", timeout=2)
                    new_status = "online" if response.status_code == 200 else "unhealthy"
                except (httpx.ConnectError, httpx.TimeoutException):
                    new_status = "offline"
                
                if new_status != previous_health[service_name]:
                    if new_status == "offline":
                        logging.warning(f"FALHA: O serviço '{service_name}' parou de responder.")
                    elif new_status == "online" and previous_health[service_name] in ["offline", "unknown"]:
                        logging.info(f"RECUPERAÇÃO: O serviço '{service_name}' voltou a operar normalmente.")
                    
                services_health[service_name] = new_status
                previous_health[service_name] = new_status
                
            await asyncio.sleep(5)

@app.on_event("startup")
def startup_event():
    asyncio.create_task(heartbeat_checker())

@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    swagger_ports = {"users": "5001", "products": "5002", "orders": "5003"}
    cards = ""
    for name, status in services_health.items():
        color = "#4CAF50" if status == "online" else "#F44336" if status == "offline" else "#9E9E9E"
        port = swagger_ports.get(name, "5000")
        
        cards += f"""
        <a href="https://127.0.0.1:{port}/docs" target="_blank" style="text-decoration: none;">
            <div style="background-color: {color}; color: white; padding: 20px; margin: 10px; border-radius: 8px; font-family: Arial; text-align: center; font-size: 20px; cursor: pointer; transition: 0.3s; box-shadow: 0 4px 8px rgba(0,0,0,0.2);" onmouseover="this.style.opacity=0.8" onmouseout="this.style.opacity=1">
                <strong>{name.upper()}</strong>: {status.upper()}<br>
                <span style="font-size: 14px; margin-top: 8px; display: block; color: #e0e0e0;">Abrir Swagger ↗</span>
            </div>
        </a>
        """
    
    html_content = f"""
    <html>
        <head>
            <title>Monitoramento - E-commerce</title>
            <meta http-equiv="refresh" content="5">
        </head>
        <body style="background-color: #2c3e50; padding: 50px;">
            <h1 style="color: white; text-align: center; font-family: Arial;">API Gateway - Status dos Microsserviços</h1>
            <p style="color: #bbb; text-align: center; font-family: Arial; font-size: 16px;">Clique nos cards para abrir o painel interativo (Swagger) de cada serviço</p>
            <div style="display: flex; justify-content: center; margin-top: 30px;">
                {cards}
            </div>
        </body>
    </html>
    """
    return html_content

@app.get("/gateway/health")
def get_gateway_health():
    return {"gateway": "online", "microsservicos": services_health}

@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(service: str, path: str, request: Request):
    global current_replica_index

    if service not in SERVICES:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    
    if services_health.get(service) == "offline":
        raise HTTPException(status_code=503, detail=f"O serviço '{service}' está indisponível.")

    base_url = SERVICES[service]

    if service == "products" and request.method == "GET":
        base_url = PRODUCTS_REPLICAS[current_replica_index]
        current_replica_index = (current_replica_index + 1) % len(PRODUCTS_REPLICAS)
        logging.info(f"Round-Robin: Lendo produto da réplica {base_url}")

    url = f"{base_url}/{service}/{path}" if path else f"{base_url}/{service}"
    
    body = await request.body()
    headers = dict(request.headers)
    headers.pop("host", None)

    async with httpx.AsyncClient(verify=False) as client:
        try:
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
                params=request.query_params,
                timeout=5.0
            )
            return Response(content=response.content, status_code=response.status_code, headers=dict(response.headers))
        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Erro ao conectar ao microsserviço")