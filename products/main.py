import json
import os
import requests
import jwt
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Serviço de Produtos")

PORT = int(os.getenv("PORT", 5002))
PEER_URL = os.getenv("PEER_URL", f"http://127.0.0.1:{5012 if PORT == 5002 else 5002}")

SECRET_KEY = "chave_jwt"
ALGORITHM = "HS256"
DB_FILE = f"products_db_{PORT}.json"

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({}, f)

class ProductCreate(BaseModel):
    name: str
    price: float
    description: str

class ProductSync(BaseModel):
    id: str
    data: dict

def read_db():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def write_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.get("/health")
def health_check():
    return {"status": "ok", "port": PORT}

@app.get("/products")
def list_products():
    return read_db()

@app.get("/products/{product_id}")
def get_product(product_id: str):
    db = read_db()
    if product_id not in db:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return db[product_id]

@app.post("/products")
def create_product(product: ProductCreate, xtoken: Optional[str] = Header(None)):
    if not xtoken or not xtoken.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente ou inválido")
    
    token = xtoken.split(" ")[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Acesso negado: Requer privilégios de admin")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    
    db = read_db()
    product_id = f"prod_{len(db) + 1}"
    product_data = product.dict()

    try:
        sync_endpoint = f"{PEER_URL}/products/sync"
        response = requests.post(sync_endpoint, json={"id": product_id, "data": product_data}, timeout=2)
        if response.status_code != 200:
            raise Exception()
    except Exception:
        raise HTTPException(status_code=503, detail="Falha na replicação. Operação abortada para manter consistência.")

    db[product_id] = product_data
    write_db(db)
    
    return {"message": "Produto criado e replicado com sucesso", "id": product_id}

@app.post("/products/sync")
def sync_product(sync: ProductSync):
    db = read_db()
    db[sync.id] = sync.data
    write_db(data=db)
    return {"status": "synced"}