import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, select

from .config import CORS_ORIGINS, DATABASE_URL, JWT_SECRET, JWT_SECRET_PADRAO
from .database import Base, SessionLocal, engine
from .models import Categoria, Gasto
from .routers import auth, categorias, gastos

logger = logging.getLogger("controle_de_gastos")

CATEGORIAS_PADRAO = [
    ("Alimentação", "#f97316"),
    ("Transporte", "#3b82f6"),
    ("Moradia", "#8b5cf6"),
    ("Lazer", "#ec4899"),
    ("Saúde", "#10b981"),
    ("Outros", "#6b7280"),
]


def _atualizar_tabela_de_gastos_antiga():
    """
    A versão sem login criava a tabela de gastos sem dono (sem usuario_id).
    Como os gastos daquela versão eram só de teste, a tabela antiga é apagada
    e recriada no formato novo. Isso só acontece uma vez: depois da troca,
    a coluna usuario_id já existe e nada é apagado.
    """
    inspetor = inspect(engine)
    if not inspetor.has_table(Gasto.__tablename__):
        return
    colunas = {coluna["name"] for coluna in inspetor.get_columns(Gasto.__tablename__)}
    if "usuario_id" not in colunas:
        logger.warning("Tabela de gastos da versão sem login encontrada: recriando vazia.")
        Gasto.__table__.drop(engine)


def preparar_banco():
    """Cria as tabelas e, se o banco estiver vazio, as categorias padrão."""
    _atualizar_tabela_de_gastos_antiga()
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.scalar(select(Categoria.id).limit(1)) is None:
            db.add_all(Categoria(nome=nome, cor=cor) for nome, cor in CATEGORIAS_PADRAO)
            db.commit()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if JWT_SECRET == JWT_SECRET_PADRAO and not DATABASE_URL.startswith("sqlite"):
        logger.warning(
            "JWT_SECRET não foi definido: usando a chave padrão. "
            "Defina uma chave própria antes de publicar."
        )
    preparar_banco()
    yield


app = FastAPI(
    title="Controle de Gastos",
    description=(
        "API para registrar e organizar gastos pessoais por categoria.\n\n"
        "Para testar por aqui: crie uma conta em **POST /auth/cadastro** (ou entre em "
        "**POST /auth/login**), copie o `access_token` da resposta e cole no botão "
        "**Authorize**."
    ),
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(categorias.router)
app.include_router(gastos.router)


@app.get("/health", tags=["Status"])
def health():
    return {"status": "ok"}
