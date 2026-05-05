import time
from celery import Celery
from fastapi import HTTPException
app = Celery(
    "meu_projeto",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)


@app.task
def calcular_soma(a, b):
    time.sleep(10)
    return a + b


@app.task
def calcular_fatorial(n):
    if n < 0:
       raise HTTPException(status_code=400, detail="Número inválido")
    time.sleep(5)
    resultado = 1

    for i in range(1, n + 1):
        resultado *= i
    

    return resultado


