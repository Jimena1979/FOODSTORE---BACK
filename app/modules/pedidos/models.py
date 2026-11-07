from typing import TYPE_CHECKING

from sqlmodel import JSON, Column, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.producto.model import Producto


class DetallePedidoBase(SQLModel):
    cantidad: int = Field(ge=1, nullable=False)
    nombre_producto_snap: str = Field(max_length=150, nullable=False)
    precio_unitario_snap: float = Field(ge=0, nullable=False)
    subtotal_snap: float = Field(ge=0, nullable=False)
    personalizacion: dict | None = Field(default=None, sa_column=Column(JSON))


class DetallePedido(DetallePedidoBase, table=True):
    __tablename__ = "detalle_pedido"

    pedido_id: int = Field(foreign_key="pedidos.id", primary_key=True, nullable=False)
    producto_id: int = Field(foreign_key="productos.id", primary_key=True, nullable=False)

    # Relaciones
    pedido: "Pedido" = Relationship(back_populates="detalles")
    producto: "Producto" = Relationship(back_populates="detalles_pedido")


class PedidoBase(SQLModel):
    usuario_id: int = Field(nullable=False)
    direccion_id: int | None = Field(default=None)
    estado_codigo: str = Field(default="PENDIENTE", max_length=20, index=True, nullable=False)
    forma_pago_codigo: str = Field(default="EFECTIVO", max_length=30, nullable=False)
    
    subtotal: float = Field(default=0.0, ge=0, nullable=False)
    descuento: float = Field(default=0.0, ge=0, nullable=False)
    costo_envio: float = Field(default=0.0, ge=0, nullable=False)
    total: float = Field(default=0.0, ge=0, nullable=False)
    
    notas: str | None = Field(default=None)
    activo: bool = Field(default=True, nullable=False)


class Pedido(PedidoBase, table=True):
    __tablename__ = "pedidos"

    id: int | None = Field(default=None, primary_key=True)

    detalles: list[DetallePedido] = Relationship(
        back_populates="pedido", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )