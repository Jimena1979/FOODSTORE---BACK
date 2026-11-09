from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.categorias.models import Categoria
    from app.modules.pedidos.models import DetallePedido


class ProductoBase(SQLModel):
    nombre: str = Field(nullable=False, min_length=2, max_length=100)
    precio_base: float = Field(ge=0, nullable=False)
    descripcion: str | None = Field(default=None)
    imagen_url: str | None = Field(default=None)
    stock: int = Field(default=0, ge=0, nullable=False)
    disponible: bool = Field(default=True, nullable=False)
    activo: bool = Field(default=True, nullable=False)


class Producto(ProductoBase, table=True):
    __tablename__ = "productos"

    id: int | None = Field(default=None, primary_key=True)
    categoria_id: int = Field(foreign_key="categorias.id", nullable=False)

    # Relaciones exactas del UML (1:N con Categoria y 1:N con DetallePedido)
    categoria: Categoria | None = Relationship(back_populates="productos")
    detalles: list[DetallePedido] = Relationship(back_populates="producto")