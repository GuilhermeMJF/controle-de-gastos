from .conftest import SENHA_PADRAO


def _login(anonimo, senha, email="ana@exemplo.com"):
    return anonimo.post("/auth/login", json={"email": email, "senha": senha})


def test_bloqueia_depois_de_5_senhas_erradas(anonimo, cadastrar):
    cadastrar()
    for _ in range(5):
        assert _login(anonimo, "senha-errada").status_code == 401

    # Bloqueado: nem a senha certa entra
    resposta = _login(anonimo, SENHA_PADRAO)
    assert resposta.status_code == 429
    assert "Muitas tentativas" in resposta.json()["detail"]
    assert int(resposta.headers["Retry-After"]) > 0


def test_login_certo_zera_os_erros(anonimo, cadastrar):
    cadastrar()
    for _ in range(4):
        _login(anonimo, "senha-errada")
    assert _login(anonimo, SENHA_PADRAO).status_code == 200

    # Depois de acertar, a contagem recomeça do zero
    for _ in range(4):
        assert _login(anonimo, "senha-errada").status_code == 401
    assert _login(anonimo, SENHA_PADRAO).status_code == 200


def test_bloqueio_vale_so_para_a_conta_atacada(anonimo, cadastrar):
    cadastrar(email="ana@exemplo.com")
    cadastrar(email="bia@exemplo.com", nome="Bia")
    for _ in range(5):
        _login(anonimo, "senha-errada", email="ana@exemplo.com")

    assert _login(anonimo, SENHA_PADRAO, email="ana@exemplo.com").status_code == 429
    assert _login(anonimo, SENHA_PADRAO, email="bia@exemplo.com").status_code == 200


def test_limite_de_cadastros_por_ip(anonimo, cadastrar):
    for numero in range(5):
        cadastrar(email=f"pessoa{numero}@exemplo.com")

    resposta = anonimo.post(
        "/auth/cadastro",
        json={"nome": "Sexta", "email": "sexta@exemplo.com", "senha": SENHA_PADRAO},
    )
    assert resposta.status_code == 429


def test_limite_de_pedidos_de_nova_senha_por_ip(anonimo):
    for numero in range(5):
        resposta = anonimo.post(
            "/auth/esqueci-senha", json={"email": f"pessoa{numero}@exemplo.com"}
        )
        assert resposta.status_code == 202

    resposta = anonimo.post("/auth/esqueci-senha", json={"email": "outra@exemplo.com"})
    assert resposta.status_code == 429