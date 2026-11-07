from fastapi import APIRouter, Query, status

from app.pedido import service as pedido_service
from app.pedido.schemas import (
    DetallePedidoCreate,
    PedidoCreate,
    PedidoRead,
    PedidoUpdateEstado,
)

router = APIRouter(prefix="/pedido", tags=["Pedidos"])


@router.post("/", response_model=PedidoRead, status_code=status.HTTP_201_CREATED)
def crear_pedido(pedido: PedidoCreate):
    """Crea un nuevo pedido con sus detalles (201 o 422)."""
    return pedido_service.crear_pedido(pedido)


@router.get("/", response_model=list[PedidoRead], status_code=status.HTTP_200_OK)
def listar_pedidos(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, le=100),
    activo: bool | None = True,
):
    """Lista los pedidos registrados."""
    return pedido_service.listar_pedidos(skip, limit, activo)


@router.get("/{id}", response_model=PedidoRead, status_code=status.HTTP_200_OK)
def detalle_pedido(id: int):
    """Devuelve el detalle de un pedido por ID (404 si no existe)."""
    return pedido_service.obtener_por_id(id)


@router.post("/{id}/detalle", response_model=PedidoRead, status_code=status.HTTP_200_OK)
def agregar_detalle(id: int, item: DetallePedidoCreate):
    """Agrega un nuevo detalle / ítem a un pedido existente."""
    return pedido_service.agregar_detalle_a_pedido(id, item)


@router.put("/{id}", response_model=PedidoRead, status_code=status.HTTP_200_OK)
def actualizar_estado_pedido(id: int, data: PedidoUpdateEstado):
    """Actualiza el estado de un pedido existente."""
    return pedido_service.actualizar_estado(id, data)


@router.delete("/{id}", response_model=PedidoRead, status_code=status.HTTP_200_OK)
def eliminar_pedido(id: int):
    """Realiza la baja lógica (activo=False) del pedido."""
    return pedido_service.desactivar_pedido(id)