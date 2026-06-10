# 🛒 Mini E-commerce Distribuído

Este projeto consiste em uma arquitetura de microsserviços simplificada para um e-commerce distribuído. O ecossistema simula cenários do mundo real, abordando conceitos fundamentais de sistemas distribuídos como proxy reverso, replicação síncrona de dados, tolerância a falhas via *Heartbeat* e comunicação segura de ponta a ponta.

---

## 🏗️ Arquitetura do Sistema

O sistema é composto por 4 componentes isolados em containers Docker que se comunicam através de uma rede interna criptografada:

```text
         Cliente (Navegador / Postman / curl)
                        │
             [HTTPS] 127.0.0.1:5000
                        ▼
             ┌────────────────────┐
             │    API Gateway     │  ← Ponto de entrada único
             └─┬────────┬────────┬┘
               │        │        │
      [HTTPS]  │        │        │  [HTTPS]
        ┌──────▼─┐   ┌──▼───┐   ┌▼────────┐
        │Usuários│   │Produ-│   │Pedidos  │
        │:5001   │   │tos   │   │:5003    │
        └────────┘   │:5002 │   └─────────┘
                     └──┬───┘
                        │ [Replicação Síncrona]
                        ▼
                     ┌────────────┐
                     │Produtos (B)│
                     │:5012       │
                     └────────────┘
```

* **API Gateway (Porta 5000):** Centraliza todas as requisições externas e gerencia um subprocesso de monitoramento (*Heartbeat*).
* **Serviço de Usuários (Porta 5001):** Responsável pelo cadastro, hash de senhas (`bcrypt`) e emissão de tokens de autenticação `JWT`.
* **Serviço de Produtos (Portas 5002 e 5012):** Catálogo de itens que opera com **duas réplicas síncronas** para garantir consistência forte dos dados.
* **Serviço de Pedidos (Porta 5003):** Orquestrador de compras que consome os serviços de usuários e produtos internamente antes de consolidar o pedido.

---

## 🔒 Funcionalidades Avançadas Implementadas

1. **TLS/HTTPS Interno:** Toda a comunicação (externa e entre os microsserviços) é criptografada utilizando certificados digitais autoassinados (*Self-Signed*) gerados dinamicamente via OpenSSL no momento do build.
2. **Dashboard de Monitoramento Visual:** O Gateway expõe uma interface gráfica simples na rota raiz para acompanhar o status de saúde da infraestrutura em tempo real.
3. **Mecanismo de Heartbeat:** O Gateway checa a saúde dos serviços a cada 5 segundos. Caso alguma instância caia, o Gateway gera logs com timestamp e passa a responder automaticamente com `503 Service Unavailable`.

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
* Ter o **Docker Desktop** instalado e em execução na máquina.

### Inicialização
Abra o terminal na pasta raiz do projeto (onde está o arquivo `docker-compose.yml`) e execute o comando abaixo para construir as imagens e iniciar o ecossistema:

```bash
docker-compose up --build
```

---

## 🖥️ Como Testar e Utilizar

### ⚠️ Importante sobre o HTTPS Local
Como os certificados SSL são gerados localmente e autoassinados, ao acessar os links abaixo o seu navegador exibirá um aviso informando que *"A conexão não é particular"*. 
* **Para prosseguir:** Clique no botão **Avançado** e selecione **Ir para 127.0.0.1 (não seguro)**.

### Links Principais
* **Dashboard Visual de Monitoramento (HTTPS):** [https://127.0.0.1:5000](https://127.0.0.1:5000)
* **API Gateway (Status JSON):** [https://127.0.0.1:5000/gateway/health](https://127.0.0.1:5000/gateway/health)

### Documentação Interativa (Swagger)
Os painéis visuais do FastAPI continuam acessíveis diretamente através de suas respectivas portas mapeadas. Você pode interagir com os botões clicando diretamente nos cards do Dashboard ou acessando:
* **Swagger - Usuários:** [https://127.0.0.1:5001/docs](https://127.0.0.1:5001/docs)
* **Swagger - Produtos (Réplica A):** [https://127.0.0.1:5002/docs](https://127.0.0.1:5002/docs)
* **Swagger - Pedidos:** [https://127.0.0.1:5003/docs](https://127.0.0.1:5003/docs)

---

## 🛠️ Tecnologias Utilizadas

* **Python 3.12**
* **FastAPI** & **Uvicorn**
* **Docker** & **Docker Compose**
* **HTTPX** (Proxy e Heartbeat Assíncrono)
* **PyJWT** (Tokens de Segurança)
* **Bcrypt** (Criptografia de Senhas)
* **OpenSSL** (Geração de Certificados de Segurança)