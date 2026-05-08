import os
import time

from celery import Celery


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = Celery(
    "meu_projeto",
    broker=REDIS_URL,
    backend=REDIS_URL,
)


@app.task
def calcular_soma(a: int, b: int) -> int:
    time.sleep(10)
    return a + b


@app.task
def calcular_fatorial(n: int) -> int:
    if n < 0:
        raise ValueError("Numero invalido: o fatorial nao aceita numero negativo")

    time.sleep(5)

    resultado = 1
    for i in range(2, n + 1):
        resultado *= i

    return resultado
