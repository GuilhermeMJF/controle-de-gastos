import os

# Os testes usam SQLite em memória, então não precisam do PostgreSQL rodando.
# Precisa ser definido antes de importar o app.
os.environ["DATABASE_URL"] = "sqlite://"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client():
    # Banco limpo a cada teste; o lifespan recria tabelas e categorias padrão
    Base.metadata.drop_all(engine)
    with TestClient(app) as cliente:
        yield cliente


@pytest.fixture
def categoria_id(client):
    return client.get("/categorias").json()[0]["id"]


@pytest.fixture
def novo_gasto(client, categoria_id):
    def _criar(**campos):
        dados = {
            "descricao": "Almoço",
            "valor": 32.5,
            "data": "2026-11-10",
            "categoria_id": categoria_id,
        }
        dados.update(campos)
        resposta = client.post("/gastos", json=dados)
        assert resposta.status_code == 201, resposta.text
        return resposta.json()

    return _criar
