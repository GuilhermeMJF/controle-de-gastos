def test_criar_gasto(client, categoria_id, novo_gasto):
    gasto = novo_gasto(descricao="  Mercado  ", valor=150.9)
    assert gasto["descricao"] == "Mercado"
    assert gasto["valor"] == 150.9
    assert gasto["categoria"]["id"] == categoria_id


def test_valor_precisa_ser_positivo(client, categoria_id):
    resposta = client.post(
        "/gastos",
        json={"descricao": "X", "valor": 0, "data": "2026-11-10", "categoria_id": categoria_id},
    )
    assert resposta.status_code == 422


def test_valor_com_mais_de_duas_casas(client, categoria_id):
    resposta = client.post(
        "/gastos",
        json={"descricao": "X", "valor": 10.999, "data": "2026-11-10", "categoria_id": categoria_id},
    )
    assert resposta.status_code == 422


def test_categoria_inexistente(client):
    resposta = client.post(
        "/gastos",
        json={"descricao": "X", "valor": 10, "data": "2026-11-10", "categoria_id": 9999},
    )
    assert resposta.status_code == 422


def test_listar_ordena_do_mais_recente(client, novo_gasto):
    novo_gasto(descricao="Antigo", data="2026-10-01")
    novo_gasto(descricao="Recente", data="2026-11-05")
    descricoes = [g["descricao"] for g in client.get("/gastos").json()]
    assert descricoes == ["Recente", "Antigo"]


def test_filtrar_por_periodo(client, novo_gasto):
    novo_gasto(descricao="Outubro", data="2026-10-15")
    novo_gasto(descricao="Novembro", data="2026-11-15")
    resposta = client.get("/gastos", params={"inicio": "2026-11-01", "fim": "2026-11-30"})
    assert [g["descricao"] for g in resposta.json()] == ["Novembro"]


def test_periodo_invertido(client):
    resposta = client.get("/gastos", params={"inicio": "2026-12-01", "fim": "2026-11-01"})
    assert resposta.status_code == 422


def test_filtrar_por_categoria(client, novo_gasto):
    categorias = client.get("/categorias").json()
    primeira, segunda = categorias[0]["id"], categorias[1]["id"]
    novo_gasto(descricao="A", categoria_id=primeira)
    novo_gasto(descricao="B", categoria_id=segunda)
    resposta = client.get("/gastos", params={"categoria_id": segunda})
    assert [g["descricao"] for g in resposta.json()] == ["B"]


def test_atualizar_gasto(client, novo_gasto):
    gasto = novo_gasto()
    outra_categoria = client.get("/categorias").json()[-1]["id"]
    resposta = client.put(
        f"/gastos/{gasto['id']}",
        json={
            "descricao": "Jantar",
            "valor": 80,
            "data": "2026-11-11",
            "categoria_id": outra_categoria,
        },
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["descricao"] == "Jantar"
    assert corpo["valor"] == 80
    assert corpo["categoria"]["id"] == outra_categoria


def test_excluir_gasto(client, novo_gasto):
    gasto = novo_gasto()
    assert client.delete(f"/gastos/{gasto['id']}").status_code == 204
    assert client.get(f"/gastos/{gasto['id']}").status_code == 404
