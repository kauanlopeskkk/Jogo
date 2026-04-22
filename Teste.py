
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
import json
import secrets
import os
from sqlalchemy import create_engine, Column, Integer, String , Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session,declarative_base
from sqlalchemy import create_engine
from redis import Redis
from dotenv import load_dotenv
from celery import Celery
load_dotenv() 

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)


celery_app = Celery("tasks", 
                    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
                    backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
)

DATABASE_URL = "sqlite:///./ListaJogos.db"

engine = create_engine(DATABASE_URL,connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)



MEU_USUARIO = os.getenv("MEU_USUARIO",) 
MEU_SENHA = os.getenv("MEU_SENHA", )
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


security = HTTPBasic()

meu_Jogos = []

class JogoDB(Base):
    __tablename__ = "jogos"
    id = Column(Integer, primary_key=True)
    nome = Column(String)
    genero = Column(String)
    plataforma = Column(String)
    ano_lancamento = Column(Integer)
    desenvolvedora = Column(String)
    preco = Column(Float)

Base.metadata.create_all(bind=engine)


class Jogo(BaseModel):
    nome: str
    genero: str
    plataforma: str
    ano_lancamento: int
    desenvolvedora: str
    preco: float
def sessao_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def salvar_jogo_cache(jogo: Jogo):
    redis_client.set(f"jogo:{jogo.id}", json.dumps(jogo.model_dump()))

def deletar_jogo_cache(id_jogo: int):
    redis_client.delete(f"jogo:{id_jogo}")




def autenticar_usuario(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, MEU_USUARIO)
    correct_password = secrets.compare_digest(credentials.password, MEU_SENHA)
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos")
    return credentials.username

@celery_app.task
def salvar_jogo_cache_task(jogo_data):
    redis_client.set(f"jogo:{jogo_data['id']}", json.dumps(jogo_data))


@celery_app.task
def deletar_jogo_cache_task(id_jogo):
    redis_client.delete(f"jogo:{id_jogo}")

@app.get("/")
def Jogo_raiz():
    return {"mensagem": "Bem-vindo à API de Jogos!"}

@app.post("/jogos")
def adicionar_Jogo(jogo: Jogo, db: Session = Depends(sessao_db), _: HTTPBasicCredentials = Depends(autenticar_usuario)):
    db_jogo = db.query(JogoDB).filter(
        JogoDB.nome == jogo.nome,
        JogoDB.genero == jogo.genero,
        JogoDB.plataforma == jogo.plataforma,
        JogoDB.ano_lancamento == jogo.ano_lancamento,
        JogoDB.desenvolvedora == jogo.desenvolvedora,
        JogoDB.preco == jogo.preco
     ).first()
    if db_jogo:
        raise HTTPException(status_code=400, detail="Esse Jogo existe dentro do Banco de Dados")
    novo_jogo = JogoDB(
        nome=jogo.nome,
        genero=jogo.genero,
        plataforma=jogo.plataforma,
        ano_lancamento=jogo.ano_lancamento,
        desenvolvedora=jogo.desenvolvedora,
        preco=jogo.preco
    )

    db.add(novo_jogo)
    db.commit()
    db.refresh(novo_jogo)

    salvar_jogo_cache_task.delay({

        "id": novo_jogo.id,
        "nome": novo_jogo.nome,
        "genero": novo_jogo.genero,
        "plataforma": novo_jogo.plataforma,
        "ano_lancamento": novo_jogo.ano_lancamento,
        "desenvolvedora": novo_jogo.desenvolvedora,
        "preco": novo_jogo.preco

 
    })

    return {"mensagem": "Jogo adicionado com sucesso", "jogo": {
        "id": novo_jogo.id,
        "nome": novo_jogo.nome,
        "genero": novo_jogo.genero,
        "plataforma": novo_jogo.plataforma,
        "ano_lancamento": novo_jogo.ano_lancamento,
        "desenvolvedora": novo_jogo.desenvolvedora,
        "preco": novo_jogo.preco
    }}

@app.get("/debug/redis")
def debug_redis():
    chaves = redis_client.keys("jogo:*")
    jogos_cache = []
    for chave in chaves:
        valor = redis_client.get(chave)
        jogos_cache.append({chave: json.loads(valor)})
    return {"jogos_cache": jogos_cache}

@app.get("/jogos")
def listar_jogos(
    page: int = 1,
    size: int = 10,
    db: Session = Depends(sessao_db), _: HTTPBasicCredentials = Depends(autenticar_usuario)    ):

    if page < 1 or size < 1:
        raise HTTPException(status_code=400, detail="Page e size devem ser maiores que 0")

    cache_key = f"jogos:page {page}:size {size}"
    cached_jogos = redis_client.get(cache_key)

    if cached_jogos:
        return json.loads(cached_jogos)

    jogos = db.query(JogoDB).offset((page - 1) * size).limit(size).all()

    if not jogos:
        raise HTTPException(status_code=404, detail="Nenhum jogo encontrado")
    
    total_jogos = db.query(JogoDB).count()

    chupa = {
        "total": total_jogos,
        "page": page,
        "size": size,
        "jogos": [
            {
                "id": jogo.id,
                "nome": jogo.nome,
                "genero": jogo.genero,
                "plataforma": jogo.plataforma,
                "ano_lancamento": jogo.ano_lancamento,
                "desenvolvedora": jogo.desenvolvedora,
                "preco": jogo.preco
            }
            for jogo in jogos
        ]
    }
    redis_client.set(cache_key, json.dumps(chupa), ex=300)

    return chupa


@app.put("/jogos/{id_jogo}")
def atualizar_jogo(
    id_jogo: int,
    jogo: Jogo,
    db: Session = Depends(sessao_db),
    _: HTTPBasicCredentials = Depends(autenticar_usuario)
):
    db_jogo = db.query(JogoDB).filter(JogoDB.id == id_jogo).first()

    if not db_jogo:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")

    db_jogo.nome = jogo.nome
    db_jogo.genero = jogo.genero
    db_jogo.plataforma = jogo.plataforma
    db_jogo.ano_lancamento = jogo.ano_lancamento
    db_jogo.desenvolvedora = jogo.desenvolvedora
    db_jogo.preco = jogo.preco

    try:
        db.commit()
        db.refresh(db_jogo)

        salvar_jogo_cache_task.delay({
            "id": db_jogo.id,
            "nome": db_jogo.nome,
            "genero": db_jogo.genero,
            "plataforma": db_jogo.plataforma,
            "ano_lancamento": db_jogo.ano_lancamento,
            "desenvolvedora": db_jogo.desenvolvedora,
            "preco": db_jogo.preco
        })

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "mensagem": "Jogo atualizado com sucesso",
        "jogo": {
            "id": db_jogo.id,
            "nome": db_jogo.nome,
            "genero": db_jogo.genero,
            "plataforma": db_jogo.plataforma,
            "ano_lancamento": db_jogo.ano_lancamento,
            "desenvolvedora": db_jogo.desenvolvedora,
            "preco": db_jogo.preco
        }
    }


@app.delete("/jogos/{id_jogo}")
def deletar_jogo(
    id_jogo: int,
    db: Session = Depends(sessao_db),
    _: HTTPBasicCredentials = Depends(autenticar_usuario)
):
    db_jogo = db.query(JogoDB)\
        .filter(JogoDB.id == id_jogo)\
        .first()

    if not db_jogo:
        raise HTTPException(
            status_code=404,
            detail="Jogo não encontrado"
        )

    db.delete(db_jogo)
    db.commit()

    deletar_jogo_cache_task.delay(id_jogo)

    return {
        "mensagem": "Jogo deletado com sucesso"}
