import time
from celery import Celery

app = Celery(
    "tasks",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)



@app.task
def calcular_soma(a,b):
   time.sleep(5)
   return a + b

@app.task
def calcular_fatorial(n):
   time.sleep(10)
   if n < 0:
      return "Error: Número negativo não tem fatorial"
   
   resultado = 1
   for i in range(1, n + 1):
      resultado *= i
   
   print(f"Fatorial de {n} é {resultado}")
   return resultado


