from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from app import envio_email
from app.database import Base, engine
from app.main import app, preparar_banco
from app.routers import auth

from .conftest import SENHA_PADRAO

NOVA_SENHA = "nova-senha-segura-456"


@pytest.fixture
def emails(monkeypatch):
    """Em vez de enviar e-mails de verdade, guarda numa lista."""
    enviados = []

    def _guardar(para_email, para_nome, link):
        enviados.append({"email": para_email, "nome": para_nome, "link": link})

    monkeypatch.setattr(envio_email, "enviar_email_de_redefinicao", _guardar)
    return enviados


def _token_do_link(link):
    return parse_qs(urlparse(link).query)["redefinir"][0]


def _pedir_e_pegar_token(anonimo, emails, email="ana@exemplo.com"):
    resposta = anonimo.post("/auth/esqueci-senha", json={"email": email})
    assert resposta.status_code == 202
    return _token_do_link(emails[-1]["link"])


def test_pedido_envia_link_para_quem_tem_conta(anonimo, cadastrar, emails):
    cadastrar()
    resposta = anonimo.post("/auth/esqueci-senha", json={"email": "ANA@exemplo.com"})
    assert resposta.status_code == 202
    assert len(emails) == 1
    assert emails[0]["email"] == "ana@exemplo.com"
    assert emails[0]["link"].startswith("http://localhost:5173/?redefinir=")


def test_email_sem_conta_tem_a_mesma_resposta(anonimo, cadastrar, emails):
    cadastrar()
    com_conta = anonimo.post("/auth/esqueci-senha", json={"email": "ana@exemplo.com"})
    sem_conta = anonimo.post("/auth/esqueci-senha", json={"email": "bia@exemplo.com"})
    assert sem_conta.status_code == com_conta.status_code == 202
    assert sem_conta.json() == com_conta.json()
    assert len(emails) == 1  # só a Ana recebeu


def test_nao_envia_varios_emails_seguidos(anonimo, cadastrar, emails):
    cadastrar()
    for _ in range(3):
        anonimo.post("/auth/esqueci-senha", json={"email": "ana@exemplo.com"})
    assert len(emails) == 1


def test_redefinir_troca_a_senha(anonimo, cadastrar, emails):
    cadastrar()
    token = _pedir_e_pegar_token(anonimo, emails)

    resposta = anonimo.post(
        "/auth/redefinir-senha", json={"token": token, "nova_senha": NOVA_SENHA}
    )
    assert resposta.status_code == 200

    antiga = anonimo.post("/auth/login", json={"email": "ana@exemplo.com", "senha": SENHA_PADRAO})
    nova = anonimo.post("/auth/login", json={"email": "ana@exemplo.com", "senha": NOVA_SENHA})
    assert antiga.status_code == 401
    assert nova.status_code == 200


def test_link_so_pode_ser_usado_uma_vez(anonimo, cadastrar, emails):
    cadastrar()
    token = _pedir_e_pegar_token(anonimo, emails)
    dados = {"token": token, "nova_senha": NOVA_SENHA}
    assert anonimo.post("/auth/redefinir-senha", json=dados).status_code == 200
    assert anonimo.post("/auth/redefinir-senha", json=dados).status_code == 400


def test_link_vencido(anonimo, cadastrar, emails, monkeypatch):
    cadastrar()
    token = _pedir_e_pegar_token(anonimo, emails)

    momento_real = auth._agora
    monkeypatch.setattr(auth, "_agora", lambda: momento_real() + timedelta(minutes=31))

    resposta = anonimo.post(
        "/auth/redefinir-senha", json={"token": token, "nova_senha": NOVA_SENHA}
    )
    assert resposta.status_code == 400


def test_link_inventado(anonimo, cadastrar):
    cadastrar()
    resposta = anonimo.post(
        "/auth/redefinir-senha",
        json={"token": "um-token-qualquer-inventado-123", "nova_senha": NOVA_SENHA},
    )
    assert resposta.status_code == 400


def test_nova_senha_curta(anonimo, cadastrar, emails):
    cadastrar()
    token = _pedir_e_pegar_token(anonimo, emails)
    resposta = anonimo.post("/auth/redefinir-senha", json={"token": token, "nova_senha": "123"})
    assert resposta.status_code == 422


def test_redefinir_encerra_logins_antigos(anonimo, cadastrar, emails):
    logado_antes = TestClient(app, headers=cadastrar())
    assert logado_antes.get("/gastos").status_code == 200

    token = _pedir_e_pegar_token(anonimo, emails)
    anonimo.post("/auth/redefinir-senha", json={"token": token, "nova_senha": NOVA_SENHA})

    # O login feito antes da troca deixa de valer...
    assert logado_antes.get("/gastos").status_code == 401

    # ...e um login novo funciona normalmente
    novo_login = anonimo.post(
        "/auth/login", json={"email": "ana@exemplo.com", "senha": NOVA_SENHA}
    )
    cabecalho = {"Authorization": f"Bearer {novo_login.json()['access_token']}"}
    assert TestClient(app, headers=cabecalho).get("/gastos").status_code == 200


def test_link_antigo_para_de_valer_depois_de_redefinir(anonimo, cadastrar, emails, monkeypatch):
    cadastrar()
    primeiro = _pedir_e_pegar_token(anonimo, emails)

    # Pede de novo depois do intervalo mínimo
    momento_real = auth._agora
    monkeypatch.setattr(auth, "_agora", lambda: momento_real() + timedelta(minutes=3))
    segundo = _pedir_e_pegar_token(anonimo, emails)
    assert primeiro != segundo

    anonimo.post("/auth/redefinir-senha", json={"token": segundo, "nova_senha": NOVA_SENHA})
    resposta = anonimo.post(
        "/auth/redefinir-senha", json={"token": primeiro, "nova_senha": "outra-senha-789"}
    )
    assert resposta.status_code == 400


def test_banco_antigo_ganha_a_coluna_nova():
    """Simula o banco que já está no ar, criado antes da recuperação de senha."""
    Base.metadata.drop_all(engine)
    with engine.begin() as conexao:
        conexao.execute(
            text(
                "CREATE TABLE usuarios (id INTEGER PRIMARY KEY, nome VARCHAR(80), "
                "email VARCHAR(254), senha_hash VARCHAR(255), criado_em DATETIME)"
            )
        )
        conexao.execute(
            text("INSERT INTO usuarios (nome, email, senha_hash) VALUES ('Ana', 'a@b.com', 'x')")
        )

    preparar_banco()

    colunas = {c["name"] for c in inspect(engine).get_columns("usuarios")}
    assert "versao_sessao" in colunas
    with engine.connect() as conexao:
        assert conexao.execute(text("SELECT versao_sessao FROM usuarios")).scalar() == 0
