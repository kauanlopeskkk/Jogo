from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
import secrets
import os
import json

from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import redis




DATABASE_URL = "sqlite:///./ListaJogos.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()




MEU_USUARIO = os.getenv("MEU_USUARIO", "admin")
MEU_SENHA = os.getenv("MEU_SENHA", "123")



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




redis_client = redis.Redis(
    host="redis",  
    port=6379,
    decode_responses=True
)




security = HTTPBasic()


def autenticar_usuario(credentials: HTTPBasicCredentials = Depends(security)):
    if not (
        secrets.compare_digest(credentials.username, MEU_USUARIO)
        and secrets.compare_digest(credentials.password, MEU_SENHA)
    ):
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos")

    return credentials.username



class JogoDB(Base):
    __tablename__ = "jogos"

    id = Column(Integer, primary_key=True, index=True)
    nome_jogo = Column(String, index=True)
    genero = Column(String, index=True)
    plataforma = Column(String, index=True)
    ano_lancamento = Column(Integer, index=True)
    desenvolvedora = Column(String, index=True)
    preco = Column(Float, index=True)


Base.metadata.create_all(bind=engine)


class Jogo(BaseModel):
    nome_jogo: str
    genero: str
    plataforma: str
    ano_lancamento: int
    desenvolvedora: str
    preco: float


# =========================
# DB SESSION
# =========================

def sessao_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# REDIS HELPERS (SEM ASYNC)
# =========================

def salvar_jogo_no_redis(jogo: Jogo):
    try:
        redis_client.rpush("jogos", json.dumps(jogo.dict()))
    except Exception as e:
        print(f"Erro Redis (salvar): {e}")


def deletar_jogo_do_redis(id_jogo: int):
    try:
        jogos = redis_client.lrange("jogos", 0, -1)

        for jogo in jogos:
            data = json.loads(jogo)
            if data.get("id") == id_jogo:
                redis_client.lrem("jogos", 0, jogo)
    except Exception as e:
        print(f"Erro Redis (deletar): {e}")


def limpar_cache():
    try:
        for key in redis_client.scan_iter("Jogos:page=*"):
            redis_client.delete(key)
    except Exception as e:
        print(f"Erro Redis: {e}")




@app.get("/")
def raiz():
    return {"mensagem": "Bem-vindo à API de Jogos!"}


@app.get("/redis")
def listar_jogos_redis():
    try:
        jogos = redis_client.lrange("jogos", 0, -1)
        return [json.loads(jogo) for jogo in jogos]
    except Exception as e:
        return {"erro": str(e)}


@app.post("/jogos")
def adicionar_jogo(
    jogo: Jogo,
    db: Session = Depends(sessao_db),
    _: HTTPBasicCredentials = Depends(autenticar_usuario),
):
    db_jogo = db.query(JogoDB).filter(
        JogoDB.nome_jogo == jogo.nome_jogo
    ).first()

    if db_jogo:
        raise HTTPException(status_code=400, detail="Jogo já existe")

    novo_jogo = JogoDB(**jogo.dict())

    db.add(novo_jogo)
    db.commit()
    db.refresh(novo_jogo)

    salvar_jogo_no_redis(jogo)
    limpar_cache()

    return {"mensagem": "Jogo adicionado", "id": novo_jogo.id}


@app.get("/jogos")
def listar_jogos(
    page: int = 1,
    size: int = 10,
    db: Session = Depends(sessao_db),
    _: HTTPBasicCredentials = Depends(autenticar_usuario),
):
    if page < 1 or size < 1:
        raise HTTPException(status_code=400, detail="Parâmetros inválidos")

    cache_key = f"Jogos:page={page}:size={size}"

    try:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except:
        pass

    jogos = db.query(JogoDB).offset((page - 1) * size).limit(size).all()

    if not jogos:
        raise HTTPException(status_code=404, detail="Nenhum jogo encontrado")

    total = db.query(JogoDB).count()

    resposta = {
        "page": page,
        "size": size,
        "total": total,
        "jogos": [
            {
                "id": j.id,
                "nome_jogo": j.nome_jogo,
                "genero": j.genero,
                "plataforma": j.plataforma,
                "ano_lancamento": j.ano_lancamento,
                "desenvolvedora": j.desenvolvedora,
                "preco": j.preco,
            }
            for j in jogos
        ],
    }

    try:
        redis_client.setex(cache_key, 600, json.dumps(resposta))
    except:
        pass

    return resposta


@app.put("/jogos/{id_jogo}")
def atualizar_jogo(
    id_jogo: int,
    jogo: Jogo,
    db: Session = Depends(sessao_db),
    _: HTTPBasicCredentials = Depends(autenticar_usuario),
):
    db_jogo = db.query(JogoDB).filter(JogoDB.id == id_jogo).first()

    if not db_jogo:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")

    for key, value in jogo.dict().items():
        setattr(db_jogo, key, value)

    db.commit()
    db.refresh(db_jogo)

    limpar_cache()
    salvar_jogo_no_redis(jogo)

    return {"mensagem": "Jogo atualizado"}


@app.delete("/jogos/{id_jogo}")
def deletar_jogo(
    id_jogo: int,
    db: Session = Depends(sessao_db),
    _: HTTPBasicCredentials = Depends(autenticar_usuario),
):
    db_jogo = db.query(JogoDB).filter(JogoDB.id == id_jogo).first()

    if not db_jogo:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")

    db.delete(db_jogo)
    db.commit()

    limpar_cache()
    deletar_jogo_do_redis(id_jogo)

    return {"mensagem": "Jogo deletado"}