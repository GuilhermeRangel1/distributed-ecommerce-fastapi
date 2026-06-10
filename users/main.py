import json
import os
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Serviço de Usuários")

SECRET_KEY = "chave_jwt"
ALGORITHM = "HS256"
DB_FILE = "users_db.json"

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({}, f)
class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    role: str = "user" 

class UserLogin(BaseModel):
    email: str
    password: str

def read_db():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def write_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_user_by_email(email: str):
    db = read_db()
    for user_id, user_data in db.items():
        if user_data["email"] == email:
            user_data["id"] = user_id
            return user_data
    return None


@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/users/register")
def register(user: UserRegister):
    db = read_db()
    
    if get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), salt).decode('utf-8')
    
    user_id = str(len(db) + 1)
    
    db[user_id] = {
        "name": user.name,
        "email": user.email,
        "password_hash": hashed_password,
        "role": user.role
    }
    write_db(db)
    
    return {"message": "Usuário criado com sucesso", "userId": user_id}

@app.post("/users/login")
def login(user: UserLogin):
    user_db = get_user_by_email(user.email)
    
    if not user_db or not bcrypt.checkpw(user.password.encode('utf-8'), user_db["password_hash"].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    expiration = datetime.now(timezone.utc) + timedelta(hours=2)
    payload = {
        "userId": user_db["id"],
        "email": user_db["email"],
        "role": user_db["role"],
        "exp": expiration
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return {"token": token}

@app.get("/users/{user_id}")
def get_user(user_id: str, authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente ou inválido")
    
    token = authorization.split(" ")[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    db = read_db()
    if user_id not in db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    user_data = db[user_id]
    
    return {
        "id": user_id,
        "name": user_data["name"],
        "email": user_data["email"],
        "role": user_data["role"]
    }