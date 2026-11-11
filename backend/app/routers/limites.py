import calendar
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..dependencias import get_usuario_atual
from ..models import Categoria, Gasto, Limite, Usuario
from ..schemas import (
    LimiteIn,
    LimiteOut,
    ResumoLimitesOut,
    SituacaoLimite,
    SituacaoLimiteCategoria,
)

router = APIRouter(prefix="/limites", tags=["Limites"])


def _buscar_limite(db: Session, usuario: Usuario, categoria_id: int | None) -> Limite | None:
    consulta = select(Limite).where(Limite.usuario_id == usuario.id)
    if categoria_id is None:
        consulta = consulta.where(Limite.categoria_id.is_(None))
    else:
        consulta = consulta.where(Limite.categoria_id == categoria_id)
    return db.scalar(consulta)


def _definir(db: Session, usuario: Usuario, categoria_id: int | None, valor: Decimal) -> Limite:
    """Cria o limite ou, se ele já existir, só troca o valor."""
    limite = _buscar_limite(db, usuario, categoria_id)
    if limite is None:
        limite = Limite(usuario_id=usuario.id, categoria_id=categoria_id, valor=valor)
        db.add(limite)
    else:
        limite.valor = valor
    db.commit()
    db.refresh(limite, ["categoria"])
    return limite


def _remover(db: Session, usuario: Usuario, categoria_id: int | None):
    limite = _buscar_limite(db, usuario, categoria_id)
    if limite is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nenhum limite definido")
    db.delete(limite)
    db.commit()


def _validar_categoria(db: Session, categoria_id: int):
    if db.get(Categoria, categoria_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria não encontrada")


def _intervalo_do_mes(mes: str) -> tuple[date, date]:
    ano, numero_mes = (int(parte) for parte in mes.split("-"))
    if ano < 1 or not 1 <= numero_mes <= 12:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Mês inválido")
    ultimo_dia = calendar.monthrange(ano, numero_mes)[1]
    return date(ano, numero_mes, 1), date(ano, numero_mes, ultimo_dia)


def _situacao(limite: Decimal, gasto: Decimal) -> dict:
    return {
        "limite": limite,
        "gasto": gasto,
        "porcentagem": round(float(gasto / limite * 100), 1),
        "restante": limite - gasto,
    }


@router.get("", response_model=list[LimiteOut])
def listar_limites(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    consulta = (
        select(Limite)
        .options(selectinload(Limite.categoria))
        .where(Limite.usuario_id == usuario.id)
    )
    # O limite total (sem categoria) primeiro, depois as categorias
    return sorted(db.scalars(consulta).all(), key=lambda l: l.categoria_id is not None)


@router.put("/total", response_model=LimiteOut)
def definir_limite_total(
    dados: LimiteIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    return _definir(db, usuario, None, dados.valor)


@router.delete("/total", status_code=status.HTTP_204_NO_CONTENT)
def remover_limite_total(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    _remover(db, usuario, None)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/categorias/{categoria_id}", response_model=LimiteOut)
def definir_limite_da_categoria(
    categoria_id: int,
    dados: LimiteIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    _validar_categoria(db, categoria_id)
    return _definir(db, usuario, categoria_id, dados.valor)


@router.delete("/categorias/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_limite_da_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    _remover(db, usuario, categoria_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/resumo", response_model=ResumoLimitesOut)
def resumo_do_mes(
    mes: str = Query(..., pattern=r"^\d{4}-\d{2}$", description="Mês no formato AAAA-MM"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    """Quanto já foi gasto no mês em comparação com cada limite definido."""
    inicio, fim = _intervalo_do_mes(mes)

    # Soma dos gastos do mês por categoria, calculada pelo próprio banco
    somas = db.execute(
        select(Gasto.categoria_id, func.sum(Gasto.valor))
        .where(
            Gasto.usuario_id == usuario.id,
            Gasto.data >= inicio,
            Gasto.data <= fim,
        )
        .group_by(Gasto.categoria_id)
    ).all()
    gasto_por_categoria = {categoria_id: Decimal(str(soma or 0)) for categoria_id, soma in somas}
    gasto_total = sum(gasto_por_categoria.values(), Decimal(0))

    limites = db.scalars(
        select(Limite)
        .options(selectinload(Limite.categoria))
        .where(Limite.usuario_id == usuario.id)
    ).all()

    total = None
    categorias = []
    for limite in limites:
        if limite.categoria_id is None:
            total = SituacaoLimite(**_situacao(limite.valor, gasto_total))
        else:
            gasto = gasto_por_categoria.get(limite.categoria_id, Decimal(0))
            categorias.append(
                SituacaoLimiteCategoria(
                    categoria=limite.categoria, **_situacao(limite.valor, gasto)
                )
            )

    # As categorias mais perto de estourar aparecem primeiro
    categorias.sort(key=lambda situacao: situacao.porcentagem, reverse=True)
    return ResumoLimitesOut(mes=mes, total=total, categorias=categorias)
