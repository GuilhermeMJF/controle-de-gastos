from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import Usuario
from .seguranca import ler_usuario_do_token

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

    usuario_id = ler_usuario_do_token(credenciais.credentials)
    usuario = db.get(Usuario, usuario_id) if usuario_id is not None else None
    if usuario is None:
        raise _nao_autorizado("Sessão inválida ou expirada. Entre novamente.")
    return usuario
