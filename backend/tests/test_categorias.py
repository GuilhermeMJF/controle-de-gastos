def test_categorias_padrao_sao_criadas(client):
    resposta = client.get("/categorias")
    assert resposta.status_code == 200
    nomes = [c["nome"] for c in resposta.json()]
    assert "Alimentação" in nomes
    assert len(nomes) == 6


def test_criar_categoria(client):
    resposta = client.post("/categorias", json={"nome": "Educação", "cor": "#0ea5e9"})
    assert resposta.status_code == 201
    assert resposta.json()["nome"] == "Educação"


def test_nao_permite_nome_repetido(client):
    resposta = client.post("/categorias", json={"nome": "lazer"})
    assert resposta.status_code == 409


def test_cor_invalida(client):
    resposta = client.post("/categorias", json={"nome": "Pets", "cor": "azul"})
    assert resposta.status_code == 422


def test_atualizar_categoria(client):
    nova = client.post("/categorias", json={"nome": "Educação"}).json()
    resposta = client.put(
        f"/categorias/{nova['id']}", json={"nome": "Cursos", "cor": "#111111"}
    )
    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Cursos"


def test_categorias_padrao_nao_podem_ser_alteradas(client, categoria_id):
    resposta = client.put(f"/categorias/{categoria_id}", json={"nome": "Comida"})
    assert resposta.status_code == 403
    assert client.delete(f"/categorias/{categoria_id}").status_code == 403


def test_excluir_categoria_sem_gastos(client):
    nova = client.post("/categorias", json={"nome": "Temporária"}).json()
    assert client.delete(f"/categorias/{nova['id']}").status_code == 204
    assert client.delete(f"/categorias/{nova['id']}").status_code == 404


def test_nao_exclui_categoria_com_gastos(client, novo_gasto):
    nova = client.post("/categorias", json={"nome": "Viagem"}).json()
    novo_gasto(categoria_id=nova["id"])
    resposta = client.delete(f"/categorias/{nova['id']}")
    assert resposta.status_code == 409