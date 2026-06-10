FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y openssl
RUN pip install fastapi uvicorn requests bcrypt pyjwt httpx
RUN openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 365 -nodes -subj "/CN=localhost"

COPY . .