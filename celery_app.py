from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)

celery_app = Celery(
    "tasks",
    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
    backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
)


@celery_app.task
def salvar_jogo_cache_task(redis_client, jogo_data):
    import json
    redis_client.set(
        f"jogo:{jogo_data['id']}",
        json.dumps(jogo_data)
    )


@celery_app.task
def deletar_jogo_cache_task(redis_client, id_jogo):
    redis_client.delete(f"jogo:{id_jogo}")
