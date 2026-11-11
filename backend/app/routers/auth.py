from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencias import get_usuario_atual
from ..models import Usuario
from ..schemas import LoginIn, TokenOut, UsuarioCreate, UsuarioOut
from ..seguranca import HASH_FALSO, criar_token, gerar_hash_senha, verificar_senha

router = APIRouter(prefix="/auth", tags=["Login"])


def _resposta_com_token(usuario: Usuario) -> TokenOut:
    return TokenOut(
        access_token=criar_token(usuario.id),
        usuario=UsuarioOut.model_validate(usuario),
    )


@router.post("/cadastro", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def cadastrar(dados: UsuarioCreate, db: Session = Depends(get_db)):
    if db.scalar(select(Usuario.id).where(Usuario.email == dados.email)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Esse e-mail já está cadastrado")

    usuario = Usuario(
        nome=dados.nome.strip(),
        email=dados.email,
        senha_hash=gerar_hash_senha(dados.senha),
    )
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        # Dois cadastros com o mesmo e-mail chegando ao mesmo tempo
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Esse e-mail já está cadastrado")
    db.refresh(usuario)
    return _resposta_com_token(usuario)


@router.post("/login", response_model=TokenOut)
def entrar(dados: LoginIn, db: Session = Depends(get_db)):
    usuario = db.scalar(select(Usuario).where(Usuario.email == dados.email))
    senha_ok = verificar_senha(dados.senha, usuario.senha_hash if usuario else HASH_FALSO)
    if usuario is None or not senha_ok:
        # Mesma mensagem nos dois casos, para não revelar quais e-mails existem
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha incorretos")
    return _resposta_com_token(usuario)


@router.get("/me", response_model=UsuarioOut)
def usuario_logado(usuario: Usuario = Depends(get_usuario_atual)):
    return usuario
