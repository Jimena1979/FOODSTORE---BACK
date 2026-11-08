from typing import TYPE_CHECKING, Annotated, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.categorias.models import Categoria
    from app.modules.pedidos.models import DetallePedido

class ProductoBase(SQLModel):
    nombre: Annotated[str, Field(nullable=False, min_length=2, max_length=100)]
    precio_base: Annotated[float, Field(ge=0, nullable=False)]
    descripcion: Annotated[str | None, Field(default=None)] = None
    imagen_url: Annotated[str | None, Field(default=None)] = None
    stock: Annotated[int, Field(default=0, ge=0, nullable=False)] = 0
    disponible: Annotated[bool, Field(default=True, nullable=False)] = True
    activo: Annotated[bool, Field(default=True, nullable=False)] = True

class Producto(ProductoBase, table=True):
    __tablename__ = "productos"

    id: Annotated[int | None, Field(default=None, primary_key=True)] = None
    categoria_id: Annotated[int, Field(foreign_key="categorias.id", nullable=False)]

    # Relaciones exactas del UML (1:N con Categoria y 1:N con DetallePedido)
    categoria: Annotated[Optional["Categoria"], Relationship(back_populates="productos")] = None
    detalles: Annotated[list["DetallePedido"], Relationship(back_populates="producto")] = []