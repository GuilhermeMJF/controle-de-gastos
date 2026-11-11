"""Hash de senhas e tokens de login (JWT)."""

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from .config import JWT_EXPIRA_MINUTOS, JWT_SECRET

# Parâmetros do scrypt (função de hash feita para senhas, já vem no Python)
_N, _R, _P = 2**14, 8, 1
_ALGORITMO_JWT = "HS256"


def _b64(dados: bytes) -> str:
    return base64.b64encode(dados).decode()


def gerar_hash_senha(senha: str) -> str:
    """Gera um hash com sal aleatório. A senha original nunca é guardada."""
    sal = secrets.token_bytes(16)
    resumo = hashlib.scrypt(senha.encode(), salt=sal, n=_N, r=_R, p=_P)
    return f"scrypt${_N}${_R}${_P}${_b64(sal)}${_b64(resumo)}"


def verificar_senha(senha: str, hash_salvo: str) -> bool:
    try:
        _, n, r, p, sal, resumo = hash_salvo.split("$")
        calculado = hashlib.scrypt(
            senha.encode(), salt=base64.b64decode(sal), n=int(n), r=int(r), p=int(p)
        )
    except (ValueError, TypeError):
        return False
    # compare_digest evita que o tempo de resposta revele parte do hash
    return hmac.compare_digest(calculado, base64.b64decode(resumo))


# Hash "falso" usado quando o e-mail não existe, para o login levar o mesmo
# tempo nos dois casos e não revelar quais e-mails estão cadastrados.
HASH_FALSO = gerar_hash_senha(secrets.token_urlsafe(16))


def criar_token(usuario_id: int, versao_sessao: int = 0) -> str:
    agora = datetime.now(timezone.utc)
    dados = {
        "sub": str(usuario_id),
        "ver": versao_sessao,
        "iat": agora,
        "exp": agora + timedelta(minutes=JWT_EXPIRA_MINUTOS),
    }
    return jwt.encode(dados, JWT_SECRET, algorithm=_ALGORITMO_JWT)


def ler_token(token: str) -> tuple[int, int] | None:
    """
    Devolve (id do usuário, versão da sessão), ou None se o token for inválido
    ou estiver vencido.
    """
    try:
        dados = jwt.decode(token, JWT_SECRET, algorithms=[_ALGORITMO_JWT])
        return int(dados["sub"]), int(dados.get("ver", 0))
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        return None


def gerar_token_de_redefinicao() -> tuple[str, str]:
    """Devolve (token que vai no link do e-mail, hash que fica no banco)."""
    token = secrets.token_urlsafe(32)
    return token, hash_do_token_de_redefinicao(token)


def hash_do_token_de_redefinicao(token: str) -> str:
    # O token é longo e aleatório, então um SHA-256 simples já basta.
    # Assim, mesmo quem tiver acesso ao banco não consegue usar os links.
    return hashlib.sha256(token.encode()).hexdigest()
