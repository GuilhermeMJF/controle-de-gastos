from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

# Valor em reais: validado como Decimal (sem erro de arredondamento)
# e devolvido como número no JSON, para o front-end não precisar converter.
Dinheiro = Annotated[
    Decimal,
    Field(gt=0, max_digits=12, decimal_places=2),
    PlainSerializer(float, return_type=float, when_used="json"),
]


class CategoriaBase(BaseModel):
    nome: str = Field(min_length=1, max_length=50)
    cor: str = Field(default="#6b7280", pattern=r"^#[0-9a-fA-F]{6}$")


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaOut(CategoriaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class GastoBase(BaseModel):
    descricao: str = Field(min_length=1, max_length=120)
    valor: Dinheiro
    data: date
    categoria_id: int


class GastoCreate(GastoBase):
    pass


class GastoOut(GastoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    categoria: CategoriaOut
