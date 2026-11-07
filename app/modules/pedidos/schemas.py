from pydantic import BaseModel, Field, model_validator


class DetallePedidoCreate(BaseModel):
    producto_id: int = Field(..., gt=0, json_schema_extra={"example": 1})
    cantidad: int = Field(..., ge=1, json_schema_extra={"example": 2})
    personalizacion: dict | None = Field(default=None, json_schema_extra={"example": {"sin_cebolla": True}})


class DetallePedidoRead(DetallePedidoCreate):
    pedido_id: int
    nombre_producto_snap: str
    precio_unitario_snap: float
    subtotal_snap: float

    class Config:
        from_attributes = True


class PedidoCreate(BaseModel):
    usuario_id: int = Field(..., gt=0, json_schema_extra={"example": 10})
    direccion_id: int | None = Field(default=None, json_schema_extra={"example": 3})
    estado_codigo: str = Field(default="PENDIENTE", json_schema_extra={"example": "PENDIENTE"})
    forma_pago_codigo: str = Field(default="EFECTIVO", json_schema_extra={"example": "TARJETA"})
    descuento: float = Field(default=0.0, ge=0, json_schema_extra={"example": 0.0})
    costo_envio: float = Field(default=0.0, ge=0, json_schema_extra={"example": 100.0})
    notas: str | None = Field(default=None, json_schema_extra={"example": "Dejar en recepción"})
    
    detalles: list[DetallePedidoCreate] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validar_detalles(self):
        if not self.detalles or len(self.detalles) == 0:
            raise ValueError("Un pedido debe tener al menos un DetallePedido para ser creado (RN-12).")
        return self


class PedidoUpdateEstado(BaseModel):
    estado_codigo: str = Field(..., json_schema_extra={"example": "COMPLETADO"})


class PedidoRead(BaseModel):
    id: int
    usuario_id: int
    direccion_id: int | None
    estado_codigo: str
    forma_pago_codigo: str
    subtotal: float
    descuento: float
    costo_envio: float
    total: float
    notas: str | None
    activo: bool
    detalles: list[DetallePedidoRead] = Field(default_factory=list)

    class Config:
        from_attributes = True