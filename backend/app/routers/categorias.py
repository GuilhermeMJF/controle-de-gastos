from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencias import get_usuario_atual
from ..models import Categoria, Gasto, Limite, Usuario
from ..schemas import CategoriaCreate, CategoriaOut

router = APIRouter(prefix="/categorias", tags=["Categorias"])


def _visiveis_para(usuario: Usuario):
    """Condição do SQL: categorias padrão (sem dono) ou criadas por esse usuário."""
    return or_(Categoria.usuario_id.is_(None), Categoria.usuario_id == usuario.id)


def buscar_categoria_visivel(db: Session, categoria_id: int, usuario: Usuario) -> Categoria | None:
    """
    Devolve a categoria se o usuário pode usá-la (é padrão ou é dele).
    Categoria de outra pessoa é tratada como inexistente.
    Também é usada pelas rotas de gastos e de limites.
    """
    categoria = db.get(Categoria, categoria_id)
    if categoria is None or categoria.usuario_id not in (None, usuario.id):
        return None
    return categoria


def _buscar_para_alterar(db: Session, categoria_id: int, usuario: Usuario) -> Categoria:
    categoria = buscar_categoria_visivel(db, categoria_id, usuario)
    if categoria is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria não encontrada")
    if categoria.usuario_id is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "As categorias padrão não podem ser alteradas"
        )
    return categoria


def _garantir_nome_unico(
    db: Session, nome: str, usuario: Usuario, ignorar_id: int | None = None
):
    # Só compara com as categorias que essa pessoa enxerga
    consulta = select(Categoria.id).where(
        func.lower(Categoria.nome) == nome.lower(),
        _visiveis_para(usuario),
    )
    if ignorar_id is not None:
        consulta = consulta.where(Categoria.id != ignorar_id)
    if db.scalar(consulta) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe uma categoria com esse nome")


@router.get("", response_model=list[CategoriaOut])
def listar_categorias(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    consulta = select(Categoria).where(_visiveis_para(usuario)).order_by(Categoria.nome)
    return db.scalars(consulta).all()


@router.post("", response_model=CategoriaOut, status_code=status.HTTP_201_CREATED)
def criar_categoria(
    dados: CategoriaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    nome = dados.nome.strip()
    _garantir_nome_unico(db, nome, usuario)
    categoria = Categoria(nome=nome, cor=dados.cor, usuario_id=usuario.id)
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


@router.put("/{categoria_id}", response_model=CategoriaOut)
def atualizar_categoria(
    categoria_id: int,
    dados: CategoriaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    categoria = _buscar_para_alterar(db, categoria_id, usuario)
    nome = dados.nome.strip()
    _garantir_nome_unico(db, nome, usuario, ignorar_id=categoria_id)
    categoria.nome = nome
    categoria.cor = dados.cor
    db.commit()
    db.refresh(categoria)
    return categoria


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    categoria = _buscar_para_alterar(db, categoria_id, usuario)
    em_uso = db.scalar(select(Gasto.id).where(Gasto.categoria_id == categoria_id).limit(1))
    if em_uso is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Essa categoria tem gastos cadastrados. Mude ou exclua esses gastos antes.",
        )
    # Os limites definidos para essa categoria deixam de fazer sentido
    db.execute(delete(Limite).where(Limite.categoria_id == categoria_id))
    db.delete(categoria)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)