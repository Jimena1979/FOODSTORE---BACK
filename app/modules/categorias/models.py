
from typing import TYPE_CHECKING, Annotated

from pydantic import StringConstraints
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.productos.models import Producto


# 1. Clase Base opcional para los campos compartidos de entrada/salida o modelo
class CategoriaBase(SQLModel):
    nombre: Annotated[str, StringConstraints(min_length=2, max_length=100)] = Field(index=True, unique=True)
    descripcion: str | None = Field(default=None)
    activo: bool = Field(default=True)


# 2. Clase Categoria que define la tabla SQLModel (Relación 1:N exacta del UML)
class Categoria(CategoriaBase, table=True):
    __tablename__ = "categoria"

    id: int | None = Field(default=None, primary_key=True)

    # Relación 1:N con Producto requerida por la consigna (sin tablas intermedias)
    productos: list["Producto"] = Relationship(back_populates="categoria")