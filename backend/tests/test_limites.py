import pytest
from fastapi.testclient import TestClient

from app.main import app

MES = "2026-11"


@pytest.fixture
def categorias(client):
    """Ids das categorias padrão, pelo nome."""
    return {c["nome"]: c["id"] for c in client.get("/categorias").json()}


def test_limites_exigem_login(anonimo):
    assert anonimo.get("/limites").status_code == 401
    assert anonimo.put("/limites/total", json={"valor": 100}).status_code == 401
    assert anonimo.get("/limites/resumo", params={"mes": MES}).status_code == 401


def test_comeca_sem_limites(client):
    assert client.get("/limites").json() == []
    resumo = client.get("/limites/resumo", params={"mes": MES}).json()
    assert resumo == {"mes": MES, "total": None, "categorias": []}


def test_definir_e_alterar_limite_total(client):
    resposta = client.put("/limites/total", json={"valor": 3000})
    assert resposta.status_code == 200
    assert resposta.json()["categoria_id"] is None
    assert resposta.json()["valor"] == 3000

    # Definir de novo só troca o valor, não cria outro limite
    client.put("/limites/total", json={"valor": 2500})
    limites = client.get("/limites").json()
    assert len(limites) == 1
    assert limites[0]["valor"] == 2500


def test_definir_limite_da_categoria(client, categorias):
    resposta = client.put(
        f"/limites/categorias/{categorias['Lazer']}", json={"valor": 300}
    )
    assert resposta.status_code == 200
    assert resposta.json()["categoria"]["nome"] == "Lazer"


def test_categoria_inexistente(client):
    assert client.put("/limites/categorias/9999", json={"valor": 300}).status_code == 404


def test_valor_invalido(client):
    for valor in (0, -10, 10.999):
        assert client.put("/limites/total", json={"valor": valor}).status_code == 422, valor


def test_remover_limites(client, categorias):
    client.put("/limites/total", json={"valor": 3000})
    client.put(f"/limites/categorias/{categorias['Lazer']}", json={"valor": 300})

    assert client.delete("/limites/total").status_code == 204
    assert client.delete(f"/limites/categorias/{categorias['Lazer']}").status_code == 204
    assert client.get("/limites").json() == []
    assert client.delete("/limites/total").status_code == 404


def test_resumo_do_mes(client, categorias, novo_gasto):
    client.put("/limites/total", json={"valor": 1000})
    client.put(f"/limites/categorias/{categorias['Lazer']}", json={"valor": 200})
    client.put(f"/limites/categorias/{categorias['Transporte']}", json={"valor": 500})

    novo_gasto(valor=150, categoria_id=categorias["Lazer"], data="2026-11-05")
    novo_gasto(valor=100, categoria_id=categorias["Lazer"], data="2026-11-20")
    novo_gasto(valor=600, categoria_id=categorias["Moradia"], data="2026-11-01")
    # Gastos de outros meses não contam
    novo_gasto(valor=999, categoria_id=categorias["Lazer"], data="2026-10-31")
    novo_gasto(valor=999, categoria_id=categorias["Lazer"], data="2026-12-01")

    resumo = client.get("/limites/resumo", params={"mes": MES}).json()

    assert resumo["total"] == {
        "limite": 1000,
        "gasto": 850,
        "porcentagem": 85.0,
        "restante": 150,
    }
    lazer, transporte = resumo["categorias"]  # o mais perto de estourar vem primeiro
    assert lazer["categoria"]["nome"] == "Lazer"
    assert lazer["gasto"] == 250
    assert lazer["porcentagem"] == 125.0
    assert lazer["restante"] == -50  # estourou
    assert transporte["gasto"] == 0
    assert transporte["porcentagem"] == 0


def test_mes_invalido(client):
    for mes in ("2026-13", "2026-00", "novembro", "2026-1"):
        resposta = client.get("/limites/resumo", params={"mes": mes})
        assert resposta.status_code == 422, mes


def test_cada_usuario_tem_seus_limites(client, cadastrar, novo_gasto):
    client.put("/limites/total", json={"valor": 1000})
    novo_gasto(valor=400, data="2026-11-10")

    bia = TestClient(app, headers=cadastrar(email="bia@exemplo.com", nome="Bia"))
    assert bia.get("/limites").json() == []

    bia.put("/limites/total", json={"valor": 50})
    resumo_da_bia = bia.get("/limites/resumo", params={"mes": MES}).json()
    assert resumo_da_bia["total"]["gasto"] == 0  # os gastos da Ana não entram
    assert client.get("/limites").json()[0]["valor"] == 1000


def test_excluir_categoria_remove_os_limites_dela(client):
    nova = client.post("/categorias", json={"nome": "Viagem"}).json()
    client.put(f"/limites/categorias/{nova['id']}", json={"valor": 500})

    assert client.delete(f"/categorias/{nova['id']}").status_code == 204
    assert client.get("/limites").json() == []
