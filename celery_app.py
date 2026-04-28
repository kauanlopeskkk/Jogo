import time
from celery import Celery

app = Celery(
    "meu_projeto",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
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


