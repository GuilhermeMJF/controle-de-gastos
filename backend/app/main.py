from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from .config import CORS_ORIGINS
from .database import Base, SessionLocal, engine
from .models import Categoria
from .routers import categorias, gastos

CATEGORIAS_PADRAO = [
    ("Alimentação", "#f97316"),
    ("Transporte", "#3b82f6"),
    ("Moradia", "#8b5cf6"),
    ("Lazer", "#ec4899"),
    ("Saúde", "#10b981"),
    ("Outros", "#6b7280"),
]


def preparar_banco():
    """Cria as tabelas e, se o banco estiver vazio, as categorias padrão."""
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.scalar(select(Categoria.id).limit(1)) is None:
            db.add_all(Categoria(nome=nome, cor=cor) for nome, cor in CATEGORIAS_PADRAO)
            db.commit()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    preparar_banco()
    yield


app = FastAPI(
    title="Controle de Gastos",
    description="API para registrar e organizar gastos pessoais por categoria.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categorias.router)
app.include_router(gastos.router)


@app.get("/health", tags=["Status"])
def health():
    return {"status": "ok"}
