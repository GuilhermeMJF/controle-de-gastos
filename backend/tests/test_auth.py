from fastapi.testclient import TestClient

from app.main import app

from .conftest import SENHA_PADRAO


def test_cadastro_devolve_token_e_usuario(anonimo):
    resposta = anonimo.post(
        "/auth/cadastro",
        json={"nome": "Ana", "email": "  Ana@Exemplo.com ", "senha": SENHA_PADRAO},
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["access_token"]
    assert corpo["token_type"] == "bearer"
    assert corpo["usuario"]["email"] == "ana@exemplo.com"
    assert "senha" not in corpo["usuario"]
    assert "senha_hash" not in corpo["usuario"]


def test_email_repetido(anonimo, cadastrar):
    cadastrar(email="ana@exemplo.com")
    resposta = anonimo.post(
        "/auth/cadastro",
        json={"nome": "Outra Ana", "email": "ANA@exemplo.com", "senha": SENHA_PADRAO},
    )
    assert resposta.status_code == 409


def test_senha_curta(anonimo):
    resposta = anonimo.post(
        "/auth/cadastro", json={"nome": "Ana", "email": "ana@exemplo.com", "senha": "123"}
    )
    assert resposta.status_code == 422


def test_email_invalido(anonimo):
    for email in ("sem-arroba", "ana@", "ana@semponto", "ana @exemplo.com"):
        resposta = anonimo.post(
            "/auth/cadastro", json={"nome": "Ana", "email": email, "senha": SENHA_PADRAO}
        )
        assert resposta.status_code == 422, email


def test_login_com_senha_certa(anonimo, cadastrar):
    cadastrar()
    resposta = anonimo.post(
        "/auth/login", json={"email": "ana@exemplo.com", "senha": SENHA_PADRAO}
    )
    assert resposta.status_code == 200
    assert resposta.json()["usuario"]["nome"] == "Ana"


def test_login_com_senha_errada(anonimo, cadastrar):
    cadastrar()
    resposta = anonimo.post(
        "/auth/login", json={"email": "ana@exemplo.com", "senha": "senha-errada"}
    )
    assert resposta.status_code == 401


def test_login_com_email_inexistente_tem_a_mesma_mensagem(anonimo, cadastrar):
    cadastrar()
    errada = anonimo.post("/auth/login", json={"email": "ana@exemplo.com", "senha": "x"})
    inexistente = anonimo.post("/auth/login", json={"email": "bia@exemplo.com", "senha": "x"})
    assert inexistente.status_code == 401
    assert inexistente.json() == errada.json()


def test_me(client):
    resposta = client.get("/auth/me")
    assert resposta.status_code == 200
    assert resposta.json()["email"] == "ana@exemplo.com"


def test_rotas_exigem_login(anonimo):
    for rota in ("/auth/me", "/gastos", "/categorias"):
        assert anonimo.get(rota).status_code == 401, rota


def test_token_invalido(anonimo):
    cliente = TestClient(app, headers={"Authorization": "Bearer token-falso"})
    assert cliente.get("/gastos").status_code == 401


def test_cada_usuario_ve_so_os_proprios_gastos(client, cadastrar, novo_gasto):
    gasto_da_ana = novo_gasto(descricao="Gasto da Ana")
    bia = TestClient(app, headers=cadastrar(email="bia@exemplo.com", nome="Bia"))
    novo_gasto(cliente=bia, descricao="Gasto da Bia")

    assert [g["descricao"] for g in client.get("/gastos").json()] == ["Gasto da Ana"]
    assert [g["descricao"] for g in bia.get("/gastos").json()] == ["Gasto da Bia"]

    # A Bia não consegue ver, editar nem excluir o gasto da Ana
    url = f"/gastos/{gasto_da_ana['id']}"
    assert bia.get(url).status_code == 404
    dados = {k: gasto_da_ana[k] for k in ("descricao", "valor", "data", "categoria_id")}
    assert bia.put(url, json=dados).status_code == 404
    assert bia.delete(url).status_code == 404
    assert client.get(url).status_code == 200


def test_categorias_sao_compartilhadas(client, cadastrar):
    client.post("/categorias", json={"nome": "Educação"})
    bia = TestClient(app, headers=cadastrar(email="bia@exemplo.com", nome="Bia"))
    assert "Educação" in [c["nome"] for c in bia.get("/categorias").json()]
