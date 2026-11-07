
from typing import Annotated

from pydantic import StringConstraints, field_validator
from sqlmodel import SQLModel


class CategoriaCreate(SQLModel):
    nombre: Annotated[str, StringConstraints(min_length=2, max_length=100)]
    descripcion: str | None = None

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El nombre no puede estar vacío ni contener solo espacios")
        return value


class CategoriaUpdate(SQLModel):
    # Sin el campo 'activo' (la baja lógica es por DELETE)
    nombre: Annotated[str, StringConstraints(min_length=2, max_length=100)] | None = None
    descripcion: str | None = None

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError("El nombre no puede estar vacío ni contener solo espacios")
        return value


class CategoriaRead(SQLModel):
    id: int
    nombre: str
    descripcion: str | None = None
    activo: bool
