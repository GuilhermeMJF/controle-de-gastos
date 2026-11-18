import pytest
from fastapi.testclient import TestClient

from app import config
from app.main import app
from app.database import SessionLocal
from app.models import RedefinicaoSenha

from .conftest import SENHA_PADRAO

EMAIL_ADMIN = "chefe@exemplo.com"


@pytest.fixture
def admin(cadastrar, monkeypatch):
    """Cliente logado como administrador, com uma conta comum (Ana) já criada."""
    monkeypatch.setattr(config, "ADMIN_EMAILS", {EMAIL_ADMIN})
    cadastrar(email="ana@exemplo.com", nome="Ana")
    return TestClient(app, headers=cadastrar(email=EMAIL_ADMIN, nome="Chefe"))


def _conta(admin, email="ana@exemplo.com"):
    return next(u for u in admin.get("/admin/usuarios").json() if u["email"] == email)


def _entrar(anonimo, email="ana@exemplo.com"):
    return anonimo.post("/auth/login", json={"email": email, "senha": SENHA_PADRAO})


def test_quem_nao_e_admin_nao_entra(client):
    for metodo, caminho in [
        ("get", "/admin/resumo"),
        ("get", "/admin/usuarios"),
        ("post", "/admin/usuarios/1/bloquear"),
        ("delete", "/admin/usuarios/1"),
    ]:
        assert getattr(client, metodo)(caminho).status_code == 403, caminho


def test_sem_login_nao_entra(anonimo):
    assert anonimo.get("/admin/usuarios").status_code == 401


def test_me_diz_quem_e_admin(admin, anonimo):
    assert admin.get("/auth/me").json()["admin"] is True
    assert _entrar(anonimo).json()["usuario"]["admin"] is False


def test_lista_com_busca_e_quantidade_de_gastos(admin, anonimo):
    categoria_id = admin.get("/categorias").json()[0]["id"]
    ana = TestClient(app, headers={"Authorization": "Bearer " + _entrar(anonimo).json()["access_token"]})
    ana.post("/gastos", json={"descricao": "Pão", "valor": 5, "data": "2026-11-10", "categoria_id": categoria_id})

    contas = admin.get("/admin/usuarios").json()
    assert {c["email"] for c in contas} == {"ana@exemplo.com", EMAIL_ADMIN}
    assert _conta(admin)["quantidade_gastos"] == 1
    assert "valor" not in str(contas)  # o admin não vê os gastos em si

    assert [c["email"] for c in admin.get("/admin/usuarios?busca=ANA").json()] == ["ana@exemplo.com"]
    assert admin.get("/admin/usuarios?busca=ninguem").json() == []


def test_resumo(admin):
    resumo = admin.get("/admin/resumo").json()
    assert resumo["total_contas"] == 2
    assert resumo["contas_bloqueadas"] == 0
    assert len(resumo["contas_por_mes"]) == 6
    assert resumo["contas_por_mes"][-1]["quantidade"] == 2  # as duas foram criadas agora


def test_bloquear_derruba_sessao_e_impede_login(admin, anonimo):
    token = _entrar(anonimo).json()["access_token"]
    ana_id = _conta(admin)["id"]

    assert admin.post(f"/admin/usuarios/{ana_id}/bloquear").json()["bloqueado"] is True
    assert anonimo.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401

    resposta = _entrar(anonimo)
    assert resposta.status_code == 403
    assert "bloqueada" in resposta.json()["detail"]
    # Senha errada continua com a mensagem de sempre: não revela que a conta existe
    errada = anonimo.post("/auth/login", json={"email": "ana@exemplo.com", "senha": "outra-senha-1"})
    assert errada.json()["detail"] == "E-mail ou senha incorretos"

    assert admin.get("/admin/resumo").json()["contas_bloqueadas"] == 1
    admin.post(f"/admin/usuarios/{ana_id}/desbloquear")
    assert _entrar(anonimo).status_code == 200


def test_conta_bloqueada_nao_recebe_link_de_senha(admin, anonimo):
    ana_id = _conta(admin)["id"]
    admin.post(f"/admin/usuarios/{ana_id}/bloquear")

    resposta = anonimo.post("/auth/esqueci-senha", json={"email": "ana@exemplo.com"})
    assert resposta.status_code == 202  # mesma resposta de sempre
    with SessionLocal() as db:
        assert db.query(RedefinicaoSenha).count() == 0
    assert admin.post(f"/admin/usuarios/{ana_id}/enviar-link-senha").status_code == 409


def test_enviar_link_de_senha_respeita_o_intervalo(admin):
    ana_id = _conta(admin)["id"]
    assert admin.post(f"/admin/usuarios/{ana_id}/enviar-link-senha").status_code == 200
    assert admin.post(f"/admin/usuarios/{ana_id}/enviar-link-senha").status_code == 429


def test_encerrar_sessoes(admin, anonimo):
    token = _entrar(anonimo).json()["access_token"]
    ana_id = _conta(admin)["id"]
    assert admin.post(f"/admin/usuarios/{ana_id}/encerrar-sessoes").status_code == 200
    assert anonimo.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401
    assert _entrar(anonimo).status_code == 200  # pode entrar de novo


def test_editar_nome_e_email(admin, anonimo):
    ana_id = _conta(admin)["id"]
    resposta = admin.patch(f"/admin/usuarios/{ana_id}", json={"nome": "Ana Souza", "email": " ANA2@Exemplo.com "})
    assert resposta.status_code == 200
    assert resposta.json()["email"] == "ana2@exemplo.com"
    assert _entrar(anonimo, "ana2@exemplo.com").status_code == 200

    em_uso = admin.patch(f"/admin/usuarios/{ana_id}", json={"email": EMAIL_ADMIN})
    assert em_uso.status_code == 409
    assert admin.patch(f"/admin/usuarios/{ana_id}", json={"email": "invalido"}).status_code == 422


def test_excluir_apaga_a_conta_e_os_dados(admin, anonimo):
    ana = TestClient(app, headers={"Authorization": "Bearer " + _entrar(anonimo).json()["access_token"]})
    propria = ana.post("/categorias", json={"nome": "Pets", "cor": "#123456"}).json()
    ana.post("/gastos", json={"descricao": "Ração", "valor": 80, "data": "2026-11-10", "categoria_id": propria["id"]})
    ana.put("/limites/total", json={"valor": 1000})
    ana_id = _conta(admin)["id"]

    assert admin.delete(f"/admin/usuarios/{ana_id}").status_code == 204
    assert [c["email"] for c in admin.get("/admin/usuarios").json()] == [EMAIL_ADMIN]
    assert _entrar(anonimo).status_code == 401
    # As categorias padrão continuam lá para os outros
    assert len(admin.get("/categorias").json()) == 6


def test_conta_de_admin_fica_protegida(admin):
    eu = _conta(admin, EMAIL_ADMIN)["id"]
    assert admin.delete(f"/admin/usuarios/{eu}").status_code == 403
    assert admin.post(f"/admin/usuarios/{eu}/bloquear").status_code == 403
    assert admin.patch(f"/admin/usuarios/{eu}", json={"nome": "X"}).status_code == 403
    # Mandar o próprio link de senha continua permitido
    assert admin.post(f"/admin/usuarios/{eu}/enviar-link-senha").status_code == 200


def test_conta_inexistente(admin):
    assert admin.delete("/admin/usuarios/9999").status_code == 404
