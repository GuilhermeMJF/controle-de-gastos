from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Categoria(Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(50), unique=True)
    cor: Mapped[str] = mapped_column(String(7), default="#6b7280")

    gastos: Mapped[list["Gasto"]] = relationship(back_populates="categoria")


class Gasto(Base):
    __tablename__ = "gastos"

    id: Mapped[int] = mapped_column(primary_key=True)
    descricao: Mapped[str] = mapped_column(String(120))
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    data: Mapped[date] = mapped_column(Date, index=True)
    categoria_id: Mapped[int] = mapped_column(
        ForeignKey("categorias.id", ondelete="RESTRICT"), index=True
    )

    categoria: Mapped[Categoria] = relationship(back_populates="gastos")
