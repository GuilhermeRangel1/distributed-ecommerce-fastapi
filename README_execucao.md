# Mini E-commerce Distribuído com Segurança Avançada

## Requisitos
* Docker Desktop instalado e rodando.

## Como executar o projeto
1. Abra o terminal na pasta raiz do projeto.
2. Execute o comando para construir as imagens e subir os containers:
   `docker-compose up --build`

## 🔒 Comunicação Segura (Bônus TLS/HTTPS)
Toda a comunicação do ecossistema (Gateway ↔ Microsserviços e Microsserviços ↔ Microsserviços) foi criptografada utilizando **TLS/HTTPS com certificados autoassinados (Self-Signed)** gerados dinamicamente via OpenSSL no momento do build.

### ⚠️ AVISO AO ACESSAR NO NAVEGADOR:
Ao acessar o Dashboard em `https://127.0.0.1:5000`, o navegador exibirá uma tela de aviso informando que *"A conexão não é particular"*. 
* **Como prosseguir:** Clique em **Avançado** e depois em **Ir para 127.0.0.1 (não seguro)**. 
* *Nota:* Este comportamento é totalmente esperado para ambientes de desenvolvimento local utilizando certificados gerados localmente sem uma CA pública (como Let's Encrypt).

## Endpoints Principais
* **Dashboard Visual de Monitoramento (HTTPS):** https://127.0.0.1:5000
* **API Gateway (Health Check JSON):** https://127.0.0.1:5000/gateway/health