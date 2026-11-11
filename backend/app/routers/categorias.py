from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Categoria, Gasto
from ..schemas import CategoriaCreate, CategoriaOut

router = APIRouter(prefix="/categorias", tags=["Categorias"])


def _buscar_ou_404(db: Session, categoria_id: int) -> Categoria:
    categoria = db.get(Categoria, categoria_id)
    if categoria is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria não encontrada")
    return categoria


def _garantir_nome_unico(db: Session, nome: str, ignorar_id: int | None = None):
    consulta = select(Categoria.id).where(func.lower(Categoria.nome) == nome.lower())
    if ignorar_id is not None:
        consulta = consulta.where(Categoria.id != ignorar_id)
    if db.scalar(consulta) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe uma categoria com esse nome")


@router.get("", response_model=list[CategoriaOut])
def listar_categorias(db: Session = Depends(get_db)):
    return db.scalars(select(Categoria).order_by(Categoria.nome)).all()


@router.post("", response_model=CategoriaOut, status_code=status.HTTP_201_CREATED)
def criar_categoria(dados: CategoriaCreate, db: Session = Depends(get_db)):
    nome = dados.nome.strip()
    _garantir_nome_unico(db, nome)
    categoria = Categoria(nome=nome, cor=dados.cor)
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


@router.put("/{categoria_id}", response_model=CategoriaOut)
def atualizar_categoria(categoria_id: int, dados: CategoriaCreate, db: Session = Depends(get_db)):
    categoria = _buscar_ou_404(db, categoria_id)
    nome = dados.nome.strip()
    _garantir_nome_unico(db, nome, ignorar_id=categoria_id)
    categoria.nome = nome
    categoria.cor = dados.cor
    db.commit()
    db.refresh(categoria)
    return categoria


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_categoria(categoria_id: int, db: Session = Depends(get_db)):
    categoria = _buscar_ou_404(db, categoria_id)
    em_uso = db.scalar(select(Gasto.id).where(Gasto.categoria_id == categoria_id).limit(1))
    if em_uso is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Essa categoria tem gastos cadastrados. Mude ou exclua esses gastos antes.",
        )
    db.delete(categoria)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
