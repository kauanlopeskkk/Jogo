
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
import secrets
import os
from sqlalchemy import create_engine, Column, Integer, String , Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
  


DATABASE_URL = "sqlite:///./ListaJogos.db"

engine = create_engine(DATABASE_URL,connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
MEU_USUARIO = os.getenv("MEU_USUARIO", "admin") 
MEU_SENHA = os.getenv("MEU_SENHA", "admin123")
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
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    genero = Column(String, index=True)
    plataforma = Column(String, index=True)
    ano_lancamento = Column(Integer, index=True)
    desenvolvedora = Column(String, index=True)
    preco = Column(Float, index=True)

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

def autenticar_usuario(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, MEU_USUARIO)
    correct_password = secrets.compare_digest(credentials.password, MEU_SENHA)
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos")
    return credentials.username

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
    return {"mensagem": "Jogo adicionado com sucesso", "jogo": {
        "id": novo_jogo.id,
        "nome": novo_jogo.nome,
        "genero": novo_jogo.genero,
        "plataforma": novo_jogo.plataforma,
        "ano_lancamento": novo_jogo.ano_lancamento,
        "desenvolvedora": novo_jogo.desenvolvedora,
        "preco": novo_jogo.preco
    }}
@app.get("/jogos")
def listar_Jogos(
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(sessao_db),
    _: HTTPBasicCredentials = Depends(autenticar_usuario)
):
    if page < 1 or limit < 1:
        raise HTTPException(status_code=400, detail="Parâmetros de paginação inválidos")
    
    jogos = db.query(JogoDB).offset((page - 1) * limit).limit(limit).all()
    
    if not jogos:
        raise HTTPException(status_code=404, detail="Nenhum jogo cadastrado")
    
    total_jogos = db.query(JogoDB).all()
    
    return {
        "page": page,
        "limit": limit,
        "total": total_jogos,
        "jogos": [{"id": jogo.id,"nome_jogo": jogo.nome_jogo,"genero": jogo.genero,"plataforma": jogo.plataforma,"ano_lancamento": jogo.ano_lancamento,"desenvolvedora": jogo.desenvolvedora,"preco": jogo.preco} for jogo in jogos]
    }



@app.put("/jogos/{id_jogo}")
def atualizar_Jogo(
    id_jogo: int,
    jogo: Jogo,
    db:Session = Depends(sessao_db),
    _: HTTPBasicCredentials = Depends(autenticar_usuario)
):
    db_jogo = db.query(JogoDB).filter(JogoDB.id == id_jogo).first()
    if not db_jogo:
        raise HTTPException(status_code=404, detail="Este jogo não foi encontrado no seu banco de dados")
    db_jogo.nome = jogo.nome
    db_jogo.genero = jogo.genero
    db_jogo.plataforma = jogo.plataforma
    db_jogo.ano_lancamento = jogo.ano_lancamento
    db_jogo.desenvolvedora = jogo.desenvolvedora
    db_jogo.preco = jogo.preco
    db.commit()
    db.refresh(db_jogo)
    return {"mensagem": "Jogo atualizado com sucesso", "jogo": {
        "id": db_jogo.id,
        "nome_jogo": db_jogo.nome_jogo,
        "genero": db_jogo.genero,
        "plataforma": db_jogo.plataforma,
        "ano_lancamento": db_jogo.ano_lancamento,
        "desenvolvedora": db_jogo.desenvolvedora,
        "preco": db_jogo.preco
    }}


@app.delete("/jogos/{id_jogo}")
def deletar_Jogo(id_jogo: int, db: Session = Depends(sessao_db), _: HTTPBasicCredentials = Depends(autenticar_usuario)):
    db_jogo = db.query(JogoDB).filter(JogoDB.id == id_jogo).first()
    if not db_jogo:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    db.delete(db_jogo)
    db.commit()
    return {"mensagem": "Jogo deletado com sucesso"}