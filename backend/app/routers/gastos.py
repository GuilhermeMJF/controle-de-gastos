import calendar
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..dependencias import get_usuario_atual
from ..models import Categoria, Gasto, Usuario
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
        somas.setdefault(chave, {})[categoria_id] = Decimal(str(total))

    categorias = {categoria.id: categoria for categoria in db.scalars(select(Categoria))}

    # 4. Monta a resposta, incluindo os meses sem gastos (com total zero)
    resultado = []
    for ano_mes in lista_meses:
        por_categoria = somas.get(ano_mes, {})
        mais_gastas_primeiro = sorted(
            por_categoria.items(), key=lambda item: item[1], reverse=True
        )
        resultado.append(
            MesResumo(
                mes=f"{ano_mes[0]:04d}-{ano_mes[1]:02d}",
                total=sum(por_categoria.values(), Decimal(0)),
                categorias=[
                    TotalPorCategoria(categoria=categorias[categoria_id], total=total)
                    for categoria_id, total in mais_gastas_primeiro
                ],
            )
        )

    return ResumoMensalOut(meses=resultado)


@router.get("/{gasto_id}", response_model=GastoOut)
def obter_gasto(
    gasto_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    return _buscar_ou_404(db, gasto_id, usuario)


@router.post("", response_model=GastoOut, status_code=status.HTTP_201_CREATED)
def criar_gasto(
    dados: GastoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    _validar_categoria(db, dados.categoria_id)
    gasto = Gasto(**dados.model_dump(), usuario_id=usuario.id)
    gasto.descricao = gasto.descricao.strip()
    db.add(gasto)
    db.commit()
    db.refresh(gasto, ["categoria"])
    return gasto


@router.put("/{gasto_id}", response_model=GastoOut)
def atualizar_gasto(
    gasto_id: int,
    dados: GastoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    gasto = _buscar_ou_404(db, gasto_id, usuario)
    _validar_categoria(db, dados.categoria_id)
    for campo, valor in dados.model_dump().items():
        setattr(gasto, campo, valor)
    gasto.descricao = gasto.descricao.strip()
    db.commit()
    db.refresh(gasto, ["categoria"])
    return gasto


@router.delete("/{gasto_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_gasto(
    gasto_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
):
    gasto = _buscar_ou_404(db, gasto_id, usuario)
    db.delete(gasto)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)