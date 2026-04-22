from fastapi import FastAPI
from celery_app import calcular_fatorial, calcular_soma, app as celery_app
from celery.result import AsyncResult
from pydantic import BaseModel
from redis import Redis


class SomaRequest(BaseModel):
    a: int
    b: int


class FatorialRequest(BaseModel):
    n: int


redis_client = Redis(host="redis", port=6379, db=0)


def adicionar_tarefa_recente(task_id):
    redis_client.lpush("tarefas_recentes", task_id)
    redis_client.ltrim("tarefas_recentes", 0, 9)


app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API de Cálculo!"}


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


@app.get("/resultado")
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
    calcular = []

    for task_id in task_ids:
        task_id = task_id.decode("utf-8")

        resultado = AsyncResult(task_id, app=celery_app)

        calcular.append({
            "task_id": task_id,
            "status": resultado.status,
            "result": resultado.result
        })

    return calcular