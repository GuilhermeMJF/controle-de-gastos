from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import Categoria, Gasto
from ..schemas import GastoCreate, GastoOut

router = APIRouter(prefix="/gastos", tags=["Gastos"])


def _buscar_ou_404(db: Session, gasto_id: int) -> Gasto:
    gasto = db.get(Gasto, gasto_id, options=[selectinload(Gasto.categoria)])
    if gasto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gasto não encontrado")
    return gasto


def _validar_categoria(db: Session, categoria_id: int):
    if db.get(Categoria, categoria_id) is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "A categoria informada não existe"
        )


@router.get("", response_model=list[GastoOut])
def listar_gastos(
    categoria_id: int | None = Query(None, description="Filtra por categoria"),
    inicio: date | None = Query(None, description="Data inicial (inclusive), AAAA-MM-DD"),
    fim: date | None = Query(None, description="Data final (inclusive), AAAA-MM-DD"),
    db: Session = Depends(get_db),
):
    if inicio and fim and inicio > fim:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "A data inicial é maior que a final"
        )

    consulta = select(Gasto).options(selectinload(Gasto.categoria))
    if categoria_id is not None:
        consulta = consulta.where(Gasto.categoria_id == categoria_id)
    if inicio is not None:
        consulta = consulta.where(Gasto.data >= inicio)
    if fim is not None:
        consulta = consulta.where(Gasto.data <= fim)

    consulta = consulta.order_by(Gasto.data.desc(), Gasto.id.desc())
    return db.scalars(consulta).all()


@router.get("/{gasto_id}", response_model=GastoOut)
def obter_gasto(gasto_id: int, db: Session = Depends(get_db)):
    return _buscar_ou_404(db, gasto_id)


@router.post("", response_model=GastoOut, status_code=status.HTTP_201_CREATED)
def criar_gasto(dados: GastoCreate, db: Session = Depends(get_db)):
    _validar_categoria(db, dados.categoria_id)
    gasto = Gasto(**dados.model_dump())
    gasto.descricao = gasto.descricao.strip()
    db.add(gasto)
    db.commit()
    db.refresh(gasto, ["categoria"])
    return gasto


@router.put("/{gasto_id}", response_model=GastoOut)
def atualizar_gasto(gasto_id: int, dados: GastoCreate, db: Session = Depends(get_db)):
    gasto = _buscar_ou_404(db, gasto_id)
    _validar_categoria(db, dados.categoria_id)
    for campo, valor in dados.model_dump().items():
        setattr(gasto, campo, valor)
    gasto.descricao = gasto.descricao.strip()
    db.commit()
    db.refresh(gasto, ["categoria"])
    return gasto


@router.delete("/{gasto_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_gasto(gasto_id: int, db: Session = Depends(get_db)):
    gasto = _buscar_ou_404(db, gasto_id)
    db.delete(gasto)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
