import json
import os
import requests
import jwt
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Serviço de Pedidos")

PORT = 5003
DB_FILE = "orders_db.json"
USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "https://users:5001")
PRODUCTS_SERVICE_URL = os.getenv("PRODUCTS_SERVICE_URL", "https://products-replica-a:5002")

SECRET_KEY = os.getenv("JWT_SECRET", "chave_jwt")
ALGORITHM = "HS256"

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({}, f)

class OrderCreate(BaseModel):
    user_id: str
    product_id: str
    quantity: int = 1

def read_db():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def write_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/orders")
def create_order(order: OrderCreate, xtoken: Optional[str] = Header(None)):
    if not xtoken:
        raise HTTPException(status_code=401, detail="Token ausente")

    headers = {"authorization": xtoken}
    
    try:
        user_resp = requests.get(f"{USERS_SERVICE_URL}/users/{order.user_id}", headers=headers, verify=False)
        if user_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Usuário inválido ou token expirado")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=500, detail="Serviço de Usuários fora do ar")

    try:
        prod_resp = requests.get(f"{PRODUCTS_SERVICE_URL}/products/{order.product_id}", verify=False)
        if prod_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Produto não encontrado")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=500, detail="Serviço de Produtos fora do ar")

    product_data = prod_resp.json()
    db = read_db()
    order_id = f"ord_{len(db) + 1}"
    
    db[order_id] = {
        "user_id": order.user_id,
        "product_id": order.product_id,
        "product_name": product_data["name"],
        "total_price": product_data["price"] * order.quantity,
        "status": "Aprovado"
    }
    
    write_db(db)
    return {"message": "Pedido criado com sucesso!", "order_id": order_id, "total": db[order_id]["total_price"]}

@app.get("/orders/{user_id}")
def get_user_orders(user_id: str, xtoken: Optional[str] = Header(None)):
    # 1. Verifica formato do token
    if not xtoken or not xtoken.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente ou formato inválido")
    
    token = xtoken.split(" ")[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_user_id = payload.get("userId")
        token_role = payload.get("role")
        
        if str(token_user_id) != str(user_id) and token_role != "admin":
            raise HTTPException(status_code=403, detail="Acesso negado")
            
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    
    db = read_db()
    user_orders = {k: v for k, v in db.items() if v["user_id"] == user_id}
    return user_orders