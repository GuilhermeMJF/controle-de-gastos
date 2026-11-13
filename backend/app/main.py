import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, make_url, select, text

from .config import CORS_ORIGINS, DATABASE_URL, JWT_SECRET, JWT_SECRET_PADRAO
from .database import Base, SessionLocal, engine
from .models import Categoria, Gasto, Limite
from .routers import auth, categorias, gastos, limites

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


def _adicionar_colunas_novas():
    """
    O create_all só cria tabelas que ainda não existem; ele não adiciona colunas
    em tabelas antigas. Aqui entram as colunas criadas depois da primeira versão.
    (Quando o projeto crescer, o ideal é trocar isso por migrações com Alembic.)
    """
    colunas_novas = {
        "usuarios": {
            "versao_sessao": "ALTER TABLE usuarios ADD COLUMN versao_sessao INTEGER NOT NULL DEFAULT 0",
        },
    }
    inspetor = inspect(engine)
    for tabela, colunas in colunas_novas.items():
        if not inspetor.has_table(tabela):
            continue
        existentes = {coluna["name"] for coluna in inspetor.get_columns(tabela)}
        for coluna, comando in colunas.items():
            if coluna not in existentes:
                logger.warning("Adicionando a coluna %s.%s", tabela, coluna)
                with engine.begin() as conexao:
                    conexao.execute(text(comando))


def _separar_categorias_por_usuario():
    """
    Antes, todas as categorias eram de todos. Agora, as categorias padrão continuam
    de todos (usuario_id vazio), e as criadas por alguém passam a ser só dessa pessoa.
    Roda uma vez só: depois que a coluna usuario_id existe, não faz mais nada.
    """
    inspetor = inspect(engine)
    if not inspetor.has_table("categorias"):
        return
    colunas = {coluna["name"] for coluna in inspetor.get_columns("categorias")}
    if "usuario_id" in colunas:
        return

    logger.warning("Separando as categorias por usuário (acontece uma vez só).")
    with engine.begin() as conexao:
        conexao.execute(
            text(
                "ALTER TABLE categorias ADD COLUMN usuario_id INTEGER "
                "REFERENCES usuarios(id) ON DELETE CASCADE"
            )
        )
        # Antes, o nome não podia se repetir no banco inteiro. Agora, duas pessoas
        # podem ter uma categoria com o mesmo nome, então essa regra sai do banco.
        if engine.dialect.name == "postgresql":
            conexao.execute(
                text("ALTER TABLE categorias DROP CONSTRAINT IF EXISTS categorias_nome_key")
            )

    nomes_padrao = {nome for nome, _ in CATEGORIAS_PADRAO}
    tem_limites = inspetor.has_table("limites")
    with SessionLocal() as db:
        for categoria in db.scalars(select(Categoria)).all():
            if categoria.nome in nomes_padrao:
                continue  # as padrão continuam de todos

            # Quem usa essa categoria: quem tem gastos ou limites nela
            donos = set(
                db.scalars(select(Gasto.usuario_id).where(Gasto.categoria_id == categoria.id))
            )
            if tem_limites:
                donos |= set(
                    db.scalars(
                        select(Limite.usuario_id).where(Limite.categoria_id == categoria.id)
                    )
                )

            if len(donos) == 1:
                categoria.usuario_id = donos.pop()  # passa a ser só dessa pessoa
            elif not donos:
                db.delete(categoria)  # ninguém usa: pode apagar
            # Se mais de uma pessoa usa, ela continua de todos, para ninguém perder dados
        db.commit()


def preparar_banco():
    """Cria as tabelas e, se não houver nenhuma, as categorias padrão."""
    _atualizar_tabela_de_gastos_antiga()
    _adicionar_colunas_novas()
    _separar_categorias_por_usuario()
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        padrao = select(Categoria.id).where(Categoria.usuario_id.is_(None)).limit(1)
        if db.scalar(padrao) is None:
            db.add_all(Categoria(nome=nome, cor=cor) for nome, cor in CATEGORIAS_PADRAO)
            db.commit()


def _banco_local() -> bool:
    """True quando o banco é o do seu computador (Docker ou testes), e não o de produção."""
    if DATABASE_URL.startswith("sqlite"):
        return True
    return make_url(DATABASE_URL).host in ("localhost", "127.0.0.1", "db")


def _conferir_chave_do_token():
    if JWT_SECRET != JWT_SECRET_PADRAO:
        return
    if _banco_local():
        logger.warning("JWT_SECRET não foi definido: usando a chave de desenvolvimento.")
        return
    raise RuntimeError(
        "JWT_SECRET não foi definido. Defina essa variável com um valor longo e "
        "aleatório antes de publicar a API."
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _conferir_chave_do_token()
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
    version="0.4.0",
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
app.include_router(limites.router)


@app.get("/health", tags=["Status"])
def health():
    return {"status": "ok"}