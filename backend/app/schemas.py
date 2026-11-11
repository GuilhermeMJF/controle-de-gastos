from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, PlainSerializer


def _normalizar_email(valor: str) -> str:
    email = valor.strip().lower()
    usuario, _, dominio = email.partition("@")
    if (
        not usuario
        or "@" in dominio
        or "." not in dominio
        or dominio.startswith(".")
        or dominio.endswith(".")
        or any(c.isspace() for c in email)
    ):
        raise ValueError("E-mail inválido")
    return email


Email = Annotated[str, Field(max_length=254), AfterValidator(_normalizar_email)]


class UsuarioCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=80)
    email: Email
    senha: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: Email
    senha: str = Field(min_length=1, max_length=128)


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: str


class EsqueciSenhaIn(BaseModel):
    email: Email


class RedefinirSenhaIn(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    nova_senha: str = Field(min_length=8, max_length=128)


class MensagemOut(BaseModel):
    mensagem: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut

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
