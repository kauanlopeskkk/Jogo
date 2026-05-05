# 🚀 Projeto FastAPI + Celery + Redis

Este projeto implementa uma API utilizando **FastAPI** com processamento assíncrono através do **Celery** e **Redis** como broker e backend de resultados.

A aplicação permite executar tarefas demoradas de forma assíncrona, simulando processamento com `time.sleep()`.

---

## 📌 Funcionalidades

* Cálculo de soma assíncrona
* Cálculo de fatorial assíncrono
* Consulta de status e resultado de tarefas
* Listagem de tarefas recentes
* Simulação de tarefas demoradas

---

## 🛠️ Tecnologias utilizadas

* Python 3
* FastAPI
* Celery
* Redis
* Docker / Docker Compose
* Pydantic

---

## 📁 Estrutura do projeto

```
.
├── fatorial.py
├── celery_app.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## ⚙️ Como executar o projeto

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd nome-do-projeto
```

---

### 2. Subir os containers

```bash
docker compose up --build
```

---

## 🔧 Serviços executados

### API FastAPI

Acesse:

```
http://localhost:8000
```

Documentação interativa:

```
http://localhost:8000/docs
```

---

### Redis

Utilizado como:

* Broker do Celery
* Backend de resultados
* Armazenamento de tarefas recentes

---

### Celery Worker

Responsável pelo processamento assíncrono das tarefas.

---

## 📡 Endpoints disponíveis

---

### 🔹 GET /

Retorna mensagem inicial da API

---

### 🔹 POST /calcular_soma

**Body:**

```json
{
  "a": 10,
  "b": 20
}
```

---

### 🔹 POST /calcular_fatorial

**Body:**

```json
{
  "n": 5
}
```

---

### 🔹 GET /resultado/{task_id}

Consulta o status e resultado da tarefa.

---

### 🔹 GET /resultado/recentes

Lista as últimas tarefas executadas.

---

### 🔹 GET /debug/redis

Endpoint para debug (uso apenas acadêmico).

---

## 🧪 Como testar a aplicação

### 1. Criar uma tarefa

Exemplo:

```
POST /calcular_fatorial
```

Resposta:

```json
{
  "message": "Tarefa de fatorial iniciada",
  "task_id": "abc123"
}
```

---

### 2. Consultar imediatamente (task em execução)

```
GET /resultado/abc123
```

Resposta:

```json
{
  "task_id": "abc123",
  "status": "PENDING",
  "result": null
}
```

---

### 3. Consultar após alguns segundos

(aguarde ~5 segundos por causa do `time.sleep()`)

```json
{
  "task_id": "abc123",
  "status": "SUCCESS",
  "result": 120
}
```

---

## ⏱️ Simulação de processamento

As tarefas utilizam:

```python
time.sleep(5)
```

para simular operações demoradas e demonstrar o funcionamento do Celery.

---

## 📊 Evidências de execução

### ✔️ Fluxo testado

1. Criação de tarefa via API
2. Status inicial: `PENDING`
3. Execução no Celery Worker
4. Resultado final: `SUCCESS`

---

### ✔️ Log do Worker (exemplo)

```
Task calcular_fatorial[abc123] received
Task calcular_fatorial[abc123] succeeded in 5.01s: 120
```

---

## ⚠️ Observações

* O uso de `time.sleep()` é apenas para fins acadêmicos
* Em produção, tarefas devem representar processamento real
* Endpoint `/debug/redis` é apenas para debug

---

## 👤 Autor

Kauan
