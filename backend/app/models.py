from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Vai junto no token de login. Quando a senha é redefinida, o número aumenta
    # e todos os tokens antigos (de qualquer aparelho) deixam de valer.
    versao_sessao: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    gastos: Mapped[list["Gasto"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )


class RedefinicaoSenha(Base):
    """Pedido de "esqueci minha senha". Guarda só o hash do token enviado por e-mail."""

    __tablename__ = "redefinicoes_senha"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    usado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Categoria(Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(50))
    cor: Mapped[str] = mapped_column(String(7), default="#6b7280")
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=True
    )

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
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), index=True
    )

    categoria: Mapped[Categoria] = relationship(back_populates="gastos")
    usuario: Mapped[Usuario] = relationship(back_populates="gastos")


class Limite(Base):
    """
    Limite de gastos por mês, que vale para todos os meses até ser alterado.
    Com categoria_id vazio (None), é o limite total do mês; com categoria, vale só para ela.
    """

    __tablename__ = "limites"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), index=True
    )
    categoria_id: Mapped[int | None] = mapped_column(
        ForeignKey("categorias.id", ondelete="CASCADE"), nullable=True
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    categoria: Mapped[Categoria | None] = relationship()
