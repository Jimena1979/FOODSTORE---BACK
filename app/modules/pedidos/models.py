from datetime import UTC, datetime
from typing import TYPE_CHECKING, Annotated

from pydantic import StringConstraints
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.productos.models import Producto
    from app.modules.usuarios.models import Usuario


class DetallePedidoBase(SQLModel):
    producto_id: int = Field(foreign_key="productos.id", nullable=False)
    cantidad: int = Field(nullable=False)  # >= 1
    nombre_producto: str = Field(nullable=False)  # Copia inmutable (RN-05)
    precio_unitario: float = Field(nullable=False)  # Copia inmutable (RN-05)
    subtotal: float = Field(nullable=False)


class DetallePedido(DetallePedidoBase, table=True):
    __tablename__ = "detallepedido"

    id: int | None = Field(default=None, primary_key=True)
    pedido_id: int = Field(foreign_key="pedido.id", nullable=False)

    # Relaciones exactas del UML
    pedido: "Pedido" = Relationship(back_populates="items")
    producto: "Producto" = Relationship(back_populates="detalles")


class PedidoBase(SQLModel):
    usuario_id: int = Field(foreign_key="usuario.id", nullable=False)
    estado: str = Field(default="PENDIENTE", nullable=False)
    forma_pago: str = Field(nullable=False)
    # Restricción de longitud del UML (5 a 200 caracteres)
    direccion_entrega: Annotated[str, StringConstraints(min_length=5, max_length=200)] = Field(nullable=False)
    notas: Annotated[str | None, StringConstraints(max_length=300)] = Field(default=None)
    total: float = Field(default=0.0, nullable=False)


class Pedido(PedidoBase, table=True):
    __tablename__ = "pedido"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)

    # Relaciones exactas del UML
    usuario: "Usuario" = Relationship(back_populates="pedidos")
    items: list["DetallePedido"] = Relationship(
            back_populates="pedido", 
            sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )