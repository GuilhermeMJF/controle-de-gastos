import os

# Os testes usam SQLite em memória, então não precisam do PostgreSQL rodando.
# Precisa ser definido antes de importar o app.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "chave-usada-somente-nos-testes-automatizados"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.routers.auth import LIMITADORES  # noqa: E402

SENHA_PADRAO = "senha-segura-123"


@pytest.fixture
def anonimo():
    """Cliente sem login, com o banco limpo (o lifespan recria tabelas e categorias)."""
    Base.metadata.drop_all(engine)
    # As tentativas de login ficam na memória: zera para um teste não atrapalhar o outro
    for limitador in LIMITADORES:
        limitador.zerar()
    with TestClient(app) as cliente:
        yield cliente


@pytest.fixture
def cadastrar(anonimo):
    """Cria uma conta e devolve o cabeçalho de login dela."""

    def _cadastrar(email="ana@exemplo.com", nome="Ana", senha=SENHA_PADRAO):
        resposta = anonimo.post(
            "/auth/cadastro", json={"nome": nome, "email": email, "senha": senha}
        )
        assert resposta.status_code == 201, resposta.text
        return {"Authorization": f"Bearer {resposta.json()['access_token']}"}

    return _cadastrar


@pytest.fixture
def client(cadastrar):
    """Cliente já logado com a conta da Ana."""
    return TestClient(app, headers=cadastrar())


@pytest.fixture
def categoria_id(client):
    return client.get("/categorias").json()[0]["id"]


@pytest.fixture
def novo_gasto(client, categoria_id):
    def _criar(cliente=None, **campos):
        dados = {
            "descricao": "Almoço",
            "valor": 32.5,
            "data": "2026-11-10",
            "categoria_id": categoria_id,
        }
        dados.update(campos)
        resposta = (cliente or client).post("/gastos", json=dados)
        assert resposta.status_code == 201, resposta.text
        return resposta.json()

    return _criar