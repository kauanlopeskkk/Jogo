# fatorial.py

from fastapi import FastAPI, Query
from celery_app import calcular_fatorial, calcular_soma, app as celery_app
from celery.result import AsyncResult
from pydantic import BaseModel
from redis import Redis


class SomaRequest(BaseModel):
    a: int
    b: int


class FatorialRequest(BaseModel):
    n: int


redis_client = Redis(
    host="redis",
    port=6379,
    db=0,
    decode_responses=True
)


def adicionar_tarefa_recente(task_id: str):
    redis_client.lpush("tarefas_recentes", task_id)
    redis_client.ltrim("tarefas_recentes", 0, 9)


app = FastAPI()


@app.get("/")
def read_root():
    return {
        "message": "Bem-vindo à API de Cálculo!"
    }


@app.post("/calcular_soma")
def calcular_soma_endpoint(request: SomaRequest):
    task = calcular_soma.delay(request.a, request.b)

    adicionar_tarefa_recente(task.id)

    return {
        "message": "Tarefa de soma iniciada",
        "task_id": task.id
    }


@app.post("/calcular_fatorial")
def calcular_fatorial_endpoint(request: FatorialRequest):
    task = calcular_fatorial.delay(request.n)

    adicionar_tarefa_recente(task.id)

    return {
        "message": "Tarefa de fatorial iniciada",
        "task_id": task.id
    }


@app.get("/resultado/{task_id}")
def get_result(task_id: str):
    task = AsyncResult(task_id, app=celery_app)

    return {
        "task_id": task.id,
        "status": task.status,
        "result": task.result
    }


@app.get("/resultado/recentes")
def resultado_recentes():
    task_ids = redis_client.lrange("tarefas_recentes", 0, 9)
    resultados = []

    for task_id in task_ids:
        resultado = AsyncResult(task_id, app=celery_app)

        resultados.append({
            "task_id": task_id,
            "status": resultado.status,
            "result": resultado.result
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
                valor = f"Tipo não tratado: {tipo}"

            dados_redis.append({
                "key": key,
                "tipo": tipo,
                "valor": valor,
                "ttl": ttl
            })

        except Exception as e:
            dados_redis.append({
                "key": key,
                "erro": str(e)
            })

    return {
        "redis": dados_redis
    }
