import calendar
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..dependencias import get_usuario_atual
from ..models import Categoria, Gasto, Usuario
from .categorias import buscar_categoria_visivel
from ..schemas import (
    GastoCreate,
    GastoOut,
    MesResumo,
    ResumoMensalOut,
    TotalPorCategoria,
)

router = APIRouter(prefix="/gastos", tags=["Gastos"])


def _buscar_ou_404(db: Session, gasto_id: int, usuario: Usuario) -> Gasto:
    gasto = db.get(Gasto, gasto_id, options=[selectinload(Gasto.categoria)])
    # Gasto de outra pessoa responde igual a gasto inexistente,
    # para não revelar que aquele id existe
    if gasto is None or gasto.usuario_id != usuario.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gasto não encontrado")
    return gasto


def _validar_categoria(db: Session, categoria_id: int, usuario: Usuario):
    if buscar_categoria_visivel(db, categoria_id, usuario) is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "A categoria informada não existe"
        )


@router.get("", response_model=list[GastoOut])
def listar_gastos(
    categoria_id: int | None = Query(None, description="Filtra por categoria"),
    inicio: date | None = Query(None, description="Data inicial (inclusive), AAAA-MM-DD"),
    fim: date | None = Query(None, description="Data final (inclusive), AAAA-MM-DD"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    if inicio and fim and inicio > fim:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "A data inicial é maior que a final"
        )

    consulta = (
        select(Gasto)
        .options(selectinload(Gasto.categoria))
        .where(Gasto.usuario_id == usuario.id)
    )
    if categoria_id is not None:
        consulta = consulta.where(Gasto.categoria_id == categoria_id)
    if inicio is not None:
        consulta = consulta.where(Gasto.data >= inicio)
    if fim is not None:
        consulta = consulta.where(Gasto.data <= fim)

    consulta = consulta.order_by(Gasto.data.desc(), Gasto.id.desc())
    return db.scalars(consulta).all()


@router.get("/resumo-mensal", response_model=ResumoMensalOut)
def resumo_mensal(
    ate: str = Query(
        ..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$", description="Último mês, AAAA-MM"
    ),
    meses: int = Query(6, ge=1, le=24, description="Quantos meses mostrar"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    # 1. Monta a lista de meses, do mais antigo para o mais recente
    ano, mes = (int(parte) for parte in ate.split("-"))
    lista_meses = []
    for _ in range(meses):
        lista_meses.append((ano, mes))
        mes -= 1
        if mes == 0:  # passou de janeiro: volta para dezembro do ano anterior
            mes = 12
            ano -= 1
    lista_meses.reverse()

    primeiro_dia = date(*lista_meses[0], 1)
    ultimo_dia = date(*lista_meses[-1], calendar.monthrange(*lista_meses[-1])[1])

    # 2. O banco soma os gastos, agrupando por ano, mês e categoria
    ano_do_gasto = extract("year", Gasto.data)
    mes_do_gasto = extract("month", Gasto.data)
    linhas = db.execute(
        select(ano_do_gasto, mes_do_gasto, Gasto.categoria_id, func.sum(Gasto.valor))
        .where(
            Gasto.usuario_id == usuario.id,
            Gasto.data >= primeiro_dia,
            Gasto.data <= ultimo_dia,
        )
        .group_by(ano_do_gasto, mes_do_gasto, Gasto.categoria_id)
    ).all()

    # 3. Organiza o resultado: {(ano, mês): {id da categoria: total}}
    somas = {}
    for ano_linha, mes_linha, categoria_id, total in linhas:
        chave = (int(ano_linha), int(mes_linha))