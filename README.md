# API FastAPI com Celery e Redis

Projeto desenvolvido para demonstrar o uso de tarefas assincronas com **Celery**, utilizando **Redis** como broker e backend de resultados, integrado a uma API criada com **FastAPI**.

A API recebe uma requisicao, dispara uma tarefa para o Celery e retorna rapidamente um `task_id`. Depois, o usuario pode consultar o status e o resultado dessa tarefa.

## Objetivo do projeto

O objetivo principal e mostrar que tarefas demoradas podem ser executadas em segundo plano, sem bloquear a resposta da API.

Neste projeto foram implementadas tarefas para:

- Somar dois numeros.
- Calcular o fatorial de um numero.
- Consultar o status e resultado das tarefas.
- Listar tarefas recentes armazenadas no Redis.

## Tecnologias utilizadas

- Python
- FastAPI
- Uvicorn
- Celery
- Redis
- Docker
- Docker Compose

## Estrutura dos arquivos

```text
.
|-- celery_app.py
|-- fatorial.py
|-- docker-compose.yml
|-- dockerfile
|-- requirements.txt
|-- tests/
`-- README.md
```

## Descricao dos arquivos principais

### `celery_app.py`

Arquivo responsavel pela configuracao do Celery e pela definicao das tarefas assincronas.

Configuracao usada:

```python
broker="redis://redis:6379/0"
backend="redis://redis:6379/0"
```

Tarefas implementadas:

- `calcular_soma(a, b)`
- `calcular_fatorial(n)`

### `fatorial.py`

Arquivo que contem a aplicacao FastAPI.

Ele possui os endpoints responsaveis por:

- Receber requisicoes HTTP.
- Disparar tarefas assincronas do Celery.
- Retornar o `task_id`.
- Consultar o resultado das tarefas.

Observacao: neste projeto, o arquivo da API se chama `fatorial.py`, funcionando como o arquivo principal da aplicacao FastAPI.

## Como instalar e executar

### 1. Clonar o projeto

```bash
git clone <url-do-repositorio>
cd Jogo
```

### 2. Subir Redis, API e Celery worker

```bash
docker compose up --build
```

Esse comando sobe os seguintes servicos:

- `redis`: banco Redis usado pelo Celery.
- `api`: aplicacao FastAPI.
- `celery`: worker que executa as tarefas em segundo plano.

## URLs da aplicacao

API:

```text
http://localhost:8001
```

Swagger / documentacao interativa:

```text
http://localhost:8001/docs
```

## Endpoints disponiveis

### `GET /`

Verifica se a API esta rodando.

Exemplo:

```bash
curl http://localhost:8001/
```

Resposta esperada:

```json
{
  "message": "Bem-vindo a API de Calculo!"
}
```

### `POST /calcular_soma`

Dispara uma tarefa assincrona para somar dois numeros.

Exemplo:

```bash
curl -X POST http://localhost:8001/calcular_soma \
  -H "Content-Type: application/json" \
  -d "{\"a\": 10, \"b\": 20}"
```

Resposta esperada:

```json
{
  "message": "Tarefa de soma iniciada",
  "task_id": "id-da-tarefa"
}
```

### `POST /calcular_fatorial`

Dispara uma tarefa assincrona para calcular o fatorial de um numero.

Exemplo:

```bash
curl -X POST http://localhost:8001/calcular_fatorial \
  -H "Content-Type: application/json" \
  -d "{\"n\": 5}"
```

Resposta esperada:

```json
{
  "message": "Tarefa de fatorial iniciada",
  "task_id": "id-da-tarefa"
}
```

A resposta retorna rapidamente com o `task_id`. O calculo do fatorial continua sendo executado pelo Celery worker em segundo plano.

### `GET /resultado/{task_id}`

Consulta o status e o resultado de uma tarefa.

Exemplo:

```bash
curl http://localhost:8001/resultado/id-da-tarefa
```

Resposta enquanto a tarefa ainda esta em execucao:

```json
{
  "task_id": "id-da-tarefa",
  "status": "PENDING",
  "result": null
}
```

Resposta depois da conclusao do fatorial de 5:

```json
{
  "task_id": "id-da-tarefa",
  "status": "SUCCESS",
  "result": 120
}
```

### `GET /resultado/recentes`

Lista as tarefas recentes salvas no Redis.

Exemplo:

```bash
curl http://localhost:8001/resultado/recentes
```

### `GET /debug/redis`

Mostra dados armazenados no Redis. Esse endpoint foi criado apenas para debug academico.

## Como testar pelo Swagger

1. Acesse `http://localhost:8001/docs`.
2. Execute o endpoint `POST /calcular_fatorial`.
3. Envie o corpo:

```json
{
  "n": 5
}
```

4. Copie o `task_id` retornado.
5. Execute `GET /resultado/{task_id}` usando esse ID.
6. Aguarde alguns segundos e execute novamente ate aparecer:

```json
{
  "status": "SUCCESS",
  "result": 120
}
```

## Evidencias de teste

Para comprovar o funcionamento, inclua prints ou logs mostrando:

- O comando `docker compose up --build` executando os servicos.
- A API retornando um `task_id` no endpoint `POST /calcular_fatorial`.
- O Celery worker recebendo a tarefa.
- O endpoint `GET /resultado/{task_id}` retornando `SUCCESS`.
- O resultado correto do fatorial, por exemplo `120` para `5!`.

Exemplo de log esperado do Celery:

```text
Task celery_app.calcular_fatorial[id-da-tarefa] received
Task celery_app.calcular_fatorial[id-da-tarefa] succeeded in 5.0s: 120
```

Exemplo de resultado esperado:

```json
{
  "task_id": "id-da-tarefa",
  "status": "SUCCESS",
  "result": 120
}
```

## Por que a API nao bloqueia?

Quando o usuario chama `POST /calcular_fatorial`, a API apenas envia a tarefa para a fila do Celery e retorna o `task_id`.

O processamento real acontece no Celery worker. Assim, a API continua livre para receber outras requisicoes enquanto a tarefa esta sendo executada.

## Parar a aplicacao

Para parar os containers:

```bash
docker compose down
```
