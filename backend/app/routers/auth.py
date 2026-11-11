from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import envio_email
from ..config import FRONTEND_URL, REDEFINICAO_EXPIRA_MINUTOS
from ..database import get_db
from ..dependencias import get_usuario_atual
from ..models import RedefinicaoSenha, Usuario
from ..schemas import (
    EsqueciSenhaIn,
    LoginIn,
    MensagemOut,
    RedefinirSenhaIn,
    TokenOut,
    UsuarioCreate,
    UsuarioOut,
)
from ..seguranca import (
    HASH_FALSO,
    criar_token,
    gerar_hash_senha,
    gerar_token_de_redefinicao,
    hash_do_token_de_redefinicao,
    verificar_senha,
)

router = APIRouter(prefix="/auth", tags=["Login"])

# Para evitar spam, um novo e-mail só sai depois desse intervalo
INTERVALO_ENTRE_PEDIDOS = timedelta(minutes=2)

MENSAGEM_ESQUECI_SENHA = (
    "Se esse e-mail estiver cadastrado, você vai receber um link para criar uma nova senha. "
    "Confira também a caixa de spam."
)


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _em_utc(momento: datetime) -> datetime:
    # O SQLite devolve datas sem fuso; o PostgreSQL, com fuso. Aqui tudo vira UTC.
    return momento if momento.tzinfo else momento.replace(tzinfo=timezone.utc)


def _resposta_com_token(usuario: Usuario) -> TokenOut:
    return TokenOut(
        access_token=criar_token(usuario.id, usuario.versao_sessao),
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


@router.post(
    "/esqueci-senha", response_model=MensagemOut, status_code=status.HTTP_202_ACCEPTED
)
def esqueci_senha(
    dados: EsqueciSenhaIn,
    tarefas: BackgroundTasks,
    db: Session = Depends(get_db),
):
    usuario = db.scalar(select(Usuario).where(Usuario.email == dados.email))

    if usuario is not None:
        ultimo_pedido = db.scalar(
            select(RedefinicaoSenha.criado_em)
            .where(RedefinicaoSenha.usuario_id == usuario.id)
            .order_by(RedefinicaoSenha.criado_em.desc())
            .limit(1)
        )
        agora = _agora()
        pode_enviar = ultimo_pedido is None or agora - _em_utc(ultimo_pedido) >= INTERVALO_ENTRE_PEDIDOS

        if pode_enviar:
            token, token_hash = gerar_token_de_redefinicao()
            db.add(
                RedefinicaoSenha(
                    usuario_id=usuario.id,
                    token_hash=token_hash,
                    criado_em=agora,
                    expira_em=agora + timedelta(minutes=REDEFINICAO_EXPIRA_MINUTOS),
                )
            )
            db.commit()
            link = f"{FRONTEND_URL}/?redefinir={token}"
            # O e-mail sai depois da resposta: assim o tempo de resposta é parecido
            # com o de um e-mail não cadastrado
            tarefas.add_task(
                envio_email.enviar_email_de_redefinicao, usuario.email, usuario.nome, link
            )

    # Mesma resposta sempre, para não revelar quais e-mails estão cadastrados
    return MensagemOut(mensagem=MENSAGEM_ESQUECI_SENHA)


@router.post("/redefinir-senha", response_model=MensagemOut)
def redefinir_senha(dados: RedefinirSenhaIn, db: Session = Depends(get_db)):
    pedido = db.scalar(
        select(RedefinicaoSenha).where(
            RedefinicaoSenha.token_hash == hash_do_token_de_redefinicao(dados.token)
        )
    )
    agora = _agora()
    if pedido is None or pedido.usado_em is not None or _em_utc(pedido.expira_em) < agora:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Esse link é inválido ou já expirou. Peça um novo em \"Esqueci minha senha\".",
        )

    usuario = db.get(Usuario, pedido.usuario_id)
    usuario.senha_hash = gerar_hash_senha(dados.nova_senha)
    # Encerra os logins abertos em todos os aparelhos
    usuario.versao_sessao += 1
    # Este link e qualquer outro pedido pendente deixam de valer
    db.execute(
        update(RedefinicaoSenha)
        .where(
            RedefinicaoSenha.usuario_id == usuario.id,
            RedefinicaoSenha.usado_em.is_(None),
        )
        .values(usado_em=agora)
    )
    db.commit()
    return MensagemOut(mensagem="Senha alterada! Agora é só entrar com a nova senha.")


@router.get("/me", response_model=UsuarioOut)
def usuario_logado(usuario: Usuario = Depends(get_usuario_atual)):
    return usuario
