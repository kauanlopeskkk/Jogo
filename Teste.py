from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
import secrets
import os
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()

# =========================
# DATABASE
# =========================

DATABASE_URL = "sqlite:///./ListaJogos.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# =========================
# CREDENCIAIS
# =========================

MEU_USUARIO = os.getenv("MEU_USUARIO", "admin")
MEU_SENHA = os.getenv("MEU_SENHA", "1234")

# =========================
# APP
# =========================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# AUTH
# =========================

security = HTTPBasic()


def autenticar_usuario(
    credentials: HTTPBasicCredentials = Depends(security)
):
    usuario_correto = secrets.compare_digest(
        credentials.username,
        MEU_USUARIO
    )

    senha_correta = secrets.compare_digest(
        credentials.password,
        MEU_SENHA
    )

    if not (usuario_correto and senha_correta):
        raise HTTPException(
            status_code=401,
            detail="Usuário ou senha incorretos"
        )

    return credentials.username


# =========================
# MODEL SQLALCHEMY
# =========================

class JogoDB(Base):
    __tablename__ = "jogos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    genero = Column(String, index=True)
    plataforma = Column(String, index=True)
    desenvolvedora = Column(String, index=True)
    ano_lancamento = Column(Integer, index=True)
    preco = Column(Float, index=True)


Base.metadata.create_all(bind=engine)

# =========================
# MODEL PYDANTIC
# =========================

class Jogo(BaseModel):
    nome: str
    genero: str
    plataforma: str
    desenvolvedora: str
    ano_lancamento: int
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
# ROTA RAIZ
# =========================

@app.get("/")
def raiz():
    return {
        "mensagem": "Bem-vindo à API de Jogos!"
    }


# =========================
# CREATE
# =========================

@app.post("/jogos")
def adicionar_jogo(
    jogo: Jogo,
    db: Session = Depends(sessao_db),
    _: HTTPBasicCredentials = Depends(autenticar_usuario),
):
    jogo_existente = db.query(JogoDB).filter(
        JogoDB.nome == jogo.nome
    ).first()

    if jogo_existente:
        raise HTTPException(
            status_code=400,
            detail="Jogo já existe"
        )

    novo_jogo = JogoDB(**jogo.model_dump())

    db.add(novo_jogo)
    db.commit()
    db.refresh(novo_jogo)

    return {
        "mensagem": "Jogo adicionado com sucesso",
        "id": novo_jogo.id
    }


# =========================
# READ
# =========================

@app.get("/jogos")
def listar_jogos(
    page: int = 1,
    size: int = 10,
    db: Session = Depends(sessao_db),
    _: HTTPBasicCredentials = Depends(autenticar_usuario),
):
    if page < 1 or size < 1:
        raise HTTPException(
            status_code=400,
            detail="Parâmetros inválidos"
        )

    jogos = db.query(JogoDB)\
        .offset((page - 1) * size)\
        .limit(size)\
        .all()

    if not jogos:
        raise HTTPException(
            status_code=404,
            detail="Nenhum jogo encontrado"
        )

    total = db.query(JogoDB).count()

    return {
        "page": page,
        "size": size,
        "total": total,
        "jogos": [
            {
                "id": jogo.id,
                "nome": jogo.nome,
                "genero": jogo.genero,
                "plataforma": jogo.plataforma,
                "desenvolvedora": jogo.desenvolvedora,
                "ano_lancamento": jogo.ano_lancamento,
                "preco": jogo.preco,
            }
            for jogo in jogos
        ]
    }