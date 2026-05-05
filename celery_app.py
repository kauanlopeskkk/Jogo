import os

from celery import Celery


REDIS_URL = os.getenv("REDIS_URL", os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"))
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

app = Celery(
    "meu_projeto",
    broker=REDIS_URL,
    backend=RESULT_BACKEND,
)


@app.task
def calcular_soma(a, b):
    return a + b


@app.task
def calcular_fatorial(n):
    if n < 0:
        return "Erro: número negativo não possui fatorial"

    resultado = 1

    for i in range(1, n + 1):
        resultado *= i

    return resultado
