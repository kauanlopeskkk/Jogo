from celery.result import AsyncResult
from fastapi import FastAPI
from pydantic import BaseModel, Field
from redis import Redis

from celery_app import app as celery_app
from celery_app import calcular_fatorial, calcular_soma


class SomaRequest(BaseModel):
    a: int
    b: int


class FatorialRequest(BaseModel):
    n: int = Field(ge=0, description="Numero inteiro para calcular o fatorial")


redis_client = Redis(
    host="redis",
    port=6379,
    db=0,
    decode_responses=True,
)

app = FastAPI(title="API FastAPI com Celery e Redis")


def adicionar_tarefa_recente(task_id: str) -> None:
    redis_client.lpush("tarefas_recentes", task_id)
    redis_client.ltrim("tarefas_recentes", 0, 9)


@app.get("/")
def read_root():
    return {
        "message": "Bem-vindo a API de Calculo!"
    }


@app.post("/calcular_soma")
def calcular_soma_endpoint(request: SomaRequest):
    task = calcular_soma.delay(request.a, request.b)
    adicionar_tarefa_recente(task.id)

    return {
        "message": "Tarefa de soma iniciada",
        "task_id": task.id,
    }


@app.post("/calcular_fatorial")
def calcular_fatorial_endpoint(request: FatorialRequest):
    task = calcular_fatorial.delay(request.n)
    adicionar_tarefa_recente(task.id)

    return {
        "message": "Tarefa de fatorial iniciada",
        "task_id": task.id,
    }


@app.get("/resultado/{task_id}")
def get_result(task_id: str):
    task = AsyncResult(task_id, app=celery_app)

    return {
        "task_id": task.id,
        "status": task.status,
        "result": task.result if task.ready() and task.successful() else None,
    }


@app.get("/resultado/recentes")
def resultado_recentes():
    task_ids = redis_client.lrange("tarefas_recentes", 0, 9)
    resultados = []

    for task_id in task_ids:
        task = AsyncResult(task_id, app=celery_app)
        resultados.append({
            "task_id": task_id,
            "status": task.status,
            "result": task.result if task.ready() and task.successful() else None,
        })

    return resultados


@app.get("/debug/redis")
def debug_redis():
    dados_redis = []

    for key in redis_client.scan_iter():
        try:
            tipo = redis_client.type(key)
            ttl = redis_client.ttl(key)

            if tipo == "string":
                valor = redis_client.get(key)
            elif tipo == "list":
                valor = redis_client.lrange(key, 0, -1)
            else:
                valor = f"Tipo nao tratado: {tipo}"

            dados_redis.append({
                "key": key,
                "tipo": tipo,
                "valor": valor,
                "ttl": ttl,
            })
        except Exception as erro:
            dados_redis.append({
                "key": key,
                "erro": str(erro),
            })

    return {
        "redis": dados_redis
    }
