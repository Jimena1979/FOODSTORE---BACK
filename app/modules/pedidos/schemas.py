from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints


class ItemPedidoCreate(BaseModel):
    producto_id: int = Field(..., gt=0)
    cantidad: int = Field(..., ge=1)  # Cantidad mínima de 1 (RN-01)


class PedidoCreate(BaseModel):
    items: list[ItemPedidoCreate] = Field(..., min_length=1)  # Al menos un ítem obligatorio (RN-01)
    forma_pago: Literal["EFECTIVO", "TRANSFERENCIA"]
    direccion_entrega: Annotated[str, StringConstraints(min_length=5, max_length=200)]
    notas: Annotated[str | None, StringConstraints(max_length=300)] = Field(default=None)


class DetallePedidoRead(BaseModel):
    producto_id: int
    nombre_producto: str
    precio_unitario: float
    cantidad: int
    subtotal: float

    class Config:
        from_attributes = True


class PedidoRead(BaseModel):
    id: int
    usuario_id: int
    estado: str
    forma_pago: str
    direccion_entrega: str
    notas: str | None
    total: float
    created_at: datetime
    updated_at: datetime
    items: list[DetallePedidoRead] = Field(default_factory=list)

    class Config:
        from_attributes = True


class PedidosPaginados(BaseModel):
    total: int
    items: list[PedidoRead]


class CambioEstado(BaseModel):
    estado: Literal["PENDIENTE", "EN_PREPARACION", "ENTREGADO", "CANCELADO"]


class ResumenPedidos(BaseModel):
    pendientes: int
    en_preparacion: int
    entregados: int
    cancelados: int
    pedidos_hoy: int
    ingresos_entregados: float