"""Área de administração: só para os e-mails listados em ADMIN_EMAILS."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencias import get_admin
from ..models import Categoria, Gasto, Limite, RedefinicaoSenha, Usuario
from ..schemas import (
    ContasNoMes,
    MensagemOut,
    ResumoAdminOut,
    UsuarioAdminOut,
    UsuarioAdminUpdate,
)
from .auth import enviar_link_de_redefinicao

router = APIRouter(prefix="/admin", tags=["Administração"])
logger = logging.getLogger("controle_de_gastos")

MESES_NO_RESUMO = 6


def _registrar(admin: Usuario, acao: str, alvo: Usuario):
    logger.warning("ADMIN %s: %s a conta %s (id %s)", admin.email, acao, alvo.email, alvo.id)


def _buscar_conta(db: Session, usuario_id: int) -> Usuario:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conta não encontrada")
    return usuario


def _proteger_admin(alvo: Usuario):
    # Bloquear, editar ou excluir um administrador faria ele perder o acesso a esta área
    if alvo.admin:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Contas de administrador não podem ser alteradas por aqui"
        )


def _saida(usuario: Usuario, quantidade_gastos: int) -> UsuarioAdminOut:
    return UsuarioAdminOut(
        id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        criado_em=usuario.criado_em,
        bloqueado=usuario.bloqueado,
        admin=usuario.admin,
        quantidade_gastos=quantidade_gastos,
    )


def _com_quantidade(db: Session, usuario: Usuario) -> UsuarioAdminOut:
    quantidade = db.scalar(select(func.count(Gasto.id)).where(Gasto.usuario_id == usuario.id))
    return _saida(usuario, quantidade)


@router.get("/resumo", response_model=ResumoAdminOut)
def resumo(db: Session = Depends(get_db), _admin: Usuario = Depends(get_admin)):
    total = db.scalar(select(func.count(Usuario.id)))
    bloqueadas = db.scalar(select(func.count(Usuario.id)).where(Usuario.bloqueado))

    # Lista dos últimos meses, do mais antigo para o atual
    hoje = datetime.now(timezone.utc)
    ano, mes = hoje.year, hoje.month
    meses = []
    for _ in range(MESES_NO_RESUMO):
        meses.append(f"{ano:04d}-{mes:02d}")
        mes -= 1
        if mes == 0:
            mes, ano = 12, ano - 1
    meses.reverse()

    # shortcut: conta em Python lendo a data de todas as contas; com milhares de contas, agrupar no banco
    contagem = dict.fromkeys(meses, 0)
    for criado_em in db.scalars(select(Usuario.criado_em)):
        chave = criado_em.strftime("%Y-%m")
        if chave in contagem:
            contagem[chave] += 1

    return ResumoAdminOut(
        total_contas=total,
        contas_bloqueadas=bloqueadas,
        contas_por_mes=[ContasNoMes(mes=m, quantidade=q) for m, q in contagem.items()],
    )


@router.get("/usuarios", response_model=list[UsuarioAdminOut])
def listar_usuarios(
    busca: str = Query("", max_length=254, description="Parte do nome ou do e-mail"),
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_admin),
):
    quantidade = (
        select(Gasto.usuario_id, func.count(Gasto.id).label("quantidade"))
        .group_by(Gasto.usuario_id)
        .subquery()
    )
    consulta = (
        select(Usuario, func.coalesce(quantidade.c.quantidade, 0))
        .outerjoin(quantidade, quantidade.c.usuario_id == Usuario.id)
        .order_by(Usuario.criado_em.desc(), Usuario.id.desc())
    )
    termo = busca.strip().lower()
    if termo:
        padrao = f"%{termo}%"
        consulta = consulta.where(
            or_(func.lower(Usuario.nome).like(padrao), Usuario.email.like(padrao))
        )

    # shortcut: sem paginação; passando de umas 500 contas, vale paginar
    return [_saida(usuario, qtd) for usuario, qtd in db.execute(consulta)]


@router.patch("/usuarios/{usuario_id}", response_model=UsuarioAdminOut)
def editar_usuario(
    usuario_id: int,
    dados: UsuarioAdminUpdate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_admin),
):
    alvo = _buscar_conta(db, usuario_id)
    _proteger_admin(alvo)

    if dados.nome is not None:
        alvo.nome = dados.nome.strip()
    if dados.email is not None and dados.email != alvo.email:
        em_uso = db.scalar(select(Usuario.id).where(Usuario.email == dados.email))
        if em_uso is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Esse e-mail já está em uso por outra conta")
        alvo.email = dados.email
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Esse e-mail já está em uso por outra conta")
    db.refresh(alvo)
    _registrar(admin, "editou", alvo)
    return _com_quantidade(db, alvo)


def _mudar_bloqueio(db: Session, admin: Usuario, usuario_id: int, bloquear: bool) -> UsuarioAdminOut:
    alvo = _buscar_conta(db, usuario_id)
    _proteger_admin(alvo)
    if alvo.bloqueado != bloquear:
        alvo.bloqueado = bloquear
        if bloquear:
            alvo.versao_sessao += 1  # derruba os logins abertos na hora
        db.commit()
        db.refresh(alvo)
        _registrar(admin, "bloqueou" if bloquear else "desbloqueou", alvo)
    return _com_quantidade(db, alvo)


@router.post("/usuarios/{usuario_id}/bloquear", response_model=UsuarioAdminOut)
def bloquear(usuario_id: int, db: Session = Depends(get_db), admin: Usuario = Depends(get_admin)):
    return _mudar_bloqueio(db, admin, usuario_id, True)


@router.post("/usuarios/{usuario_id}/desbloquear", response_model=UsuarioAdminOut)
def desbloquear(usuario_id: int, db: Session = Depends(get_db), admin: Usuario = Depends(get_admin)):
    return _mudar_bloqueio(db, admin, usuario_id, False)


@router.post("/usuarios/{usuario_id}/encerrar-sessoes", response_model=MensagemOut)
def encerrar_sessoes(
    usuario_id: int, db: Session = Depends(get_db), admin: Usuario = Depends(get_admin)
):
    alvo = _buscar_conta(db, usuario_id)
    alvo.versao_sessao += 1
    db.commit()
    _registrar(admin, "encerrou as sessões de", alvo)
    return MensagemOut(mensagem=f"Sessões de {alvo.nome} encerradas.")


@router.post("/usuarios/{usuario_id}/enviar-link-senha", response_model=MensagemOut)
def enviar_link_senha(
    usuario_id: int,
    tarefas: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_admin),
):
    alvo = _buscar_conta(db, usuario_id)
    if alvo.bloqueado:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Desbloqueie a conta antes de enviar o link de nova senha"
        )
    if not enviar_link_de_redefinicao(db, alvo, tarefas):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Um link foi enviado há pouco. Tente de novo em 2 minutos.",
        )
    _registrar(admin, "enviou link de nova senha para", alvo)
    return MensagemOut(mensagem=f"Link de nova senha enviado para {alvo.email}.")


@router.delete("/usuarios/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_usuario(
    usuario_id: int, db: Session = Depends(get_db), admin: Usuario = Depends(get_admin)
):
    alvo = _buscar_conta(db, usuario_id)
    _proteger_admin(alvo)
    _registrar(admin, "excluiu", alvo)
    # Apaga na ordem certa: os gastos antes das categorias que eles usam
    for tabela in (Gasto, Limite, Categoria, RedefinicaoSenha):
        db.execute(delete(tabela).where(tabela.usuario_id == alvo.id))
    db.delete(alvo)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
