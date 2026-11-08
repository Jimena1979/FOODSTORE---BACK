from typing import Annotated

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from app.modules.categorias.schemas import CategoriaRead


class ProductoBaseSchema(SQLModel):
    nombre: Annotated[str, Field(min_length=2, max_length=100)]
    precio_base: Annotated[float, Field(ge=0)]
    descripcion: Annotated[str | None, Field(default=None)] = None
    imagen_url: Annotated[str | None, Field(default=None)] = None
    stock: Annotated[int, Field(default=0, ge=0)] = 0
    disponible: Annotated[bool, Field(default=True)] = True

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El nombre no puede estar vacío ni contener solo espacios")
        return value

class ProductoCreate(ProductoBaseSchema):
    categoria_id: int

class ProductoUpdate(SQLModel):
    nombre: Annotated[str | None, Field(default=None, min_length=2, max_length=100)] = None
    precio_base: Annotated[float | None, Field(default=None, ge=0)] = None
    descripcion: Annotated[str | None, Field(default=None)] = None
    imagen_url: Annotated[str | None, Field(default=None)] = None
    stock: Annotated[int | None, Field(default=None, ge=0)] = None
    disponible: Annotated[bool | None, Field(default=None)] = None
    categoria_id: Annotated[int | None, Field(default=None)] = None

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError("El nombre no puede estar vacío ni contener solo espacios")
        return value

class ProductoStockUpdate(SQLModel):
    stock: Annotated[int, Field(ge=0)]
    disponible: bool

class ProductoRead(ProductoBaseSchema):
    id: int
    categoria_id: int
    activo: bool
    categoria: CategoriaRead | None = None

class ProductosPaginados(SQLModel):
    total: int
    items: list[ProductoRead]
