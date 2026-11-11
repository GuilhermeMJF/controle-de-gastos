from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import Usuario
from .seguranca import ler_token

# auto_error=False: assim a mensagem de erro fica em português
_bearer = HTTPBearer(auto_error=False, description="Token recebido no login")


def _nao_autorizado(mensagem: str) -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        mensagem,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_usuario_atual(
    credenciais: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    if credenciais is None:
        raise _nao_autorizado("Faça login para continuar")

    dados = ler_token(credenciais.credentials)
    usuario = db.get(Usuario, dados[0]) if dados is not None else None
    # versao_sessao diferente: a senha foi redefinida depois desse login
    if usuario is None or dados[1] != usuario.versao_sessao:
        raise _nao_autorizado("Sessão inválida ou expirada. Entre novamente.")
    return usuario
