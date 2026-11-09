from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import get_current_active_user, require_role
from app.modules.pedidos.schemas import (
    CambioEstado,
    PedidoCreate,
    PedidoRead,
    PedidosPaginados,
    ResumenPedidos,
)
from app.modules.pedidos.service import PedidoService
from app.modules.pedidos.unit_of_work import PedidoUnitOfWork
from app.modules.usuarios.models import Usuario

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


@router.post("/", response_model=PedidoRead, status_code=status.HTTP_201_CREATED)
def crear_pedido(
    data: PedidoCreate,
    current_user: Annotated[Usuario, Depends(get_current_active_user)],
):
    """
    Crea un nuevo pedido para el usuario autenticado usando Unit of Work (RN-01, RN-05).
    """
    with PedidoUnitOfWork() as uow:
        service = PedidoService(uow)
        pedido = service.crear_pedido(usuario_id=current_user.id, data=data)
        uow.commit()
        return pedido


@router.get("/", response_model=PedidosPaginados)
def listar_pedidos(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    current_user: Annotated[Usuario, Depends(get_current_active_user)] = None,
):
    """
    Lista los pedidos. Si es cliente, solo ve los suyos. Si es admin, ve el listado general.
    """
    with PedidoUnitOfWork() as uow:
        service = PedidoService(uow)
        
        # Verificamos si es administrador basándonos en el campo role del modelo Usuario
        es_admin = current_user.role == "admin"
        usuario_id_filtro = None if es_admin else current_user.id

        pedidos, total = service.listar_pedidos(skip=skip, limit=limit, usuario_id=usuario_id_filtro)
        return {"total": total, "items": pedidos}


@router.get("/resumen", response_model=ResumenPedidos)
def obtener_resumen_pedidos(
    _admin: Annotated[Usuario, Depends(require_role(["admin"]))],
):
    """
    Obtiene las estadísticas y resumen de pedidos (requiere rol de Administrador).
    """
    with PedidoUnitOfWork() as uow:
        service = PedidoService(uow)
        return service.obtener_resumen()


@router.get("/{pedido_id}", response_model=PedidoRead)
def obtener_pedido(
    pedido_id: int,
    current_user: Annotated[Usuario, Depends(get_current_active_user)],
):
    """
    Obtiene el detalle de un pedido por su ID validando permisos.
    """
    with PedidoUnitOfWork() as uow:
        service = PedidoService(uow)
        es_admin = current_user.role == "admin"
        return service.obtener_pedido_por_id(pedido_id=pedido_id, usuario_id=current_user.id, es_admin=es_admin)


@router.patch("/{pedido_id}/estado", response_model=PedidoRead)
def cambiar_estado_pedido(
    pedido_id: int,
    estado_in: CambioEstado,
    current_user: Annotated[Usuario, Depends(get_current_active_user)],
):
    """
    Cambia el estado de un pedido (cancela el cliente si está pendiente o avanza el admin) con UoW.
    """
    with PedidoUnitOfWork() as uow:
        service = PedidoService(uow)
        es_admin = current_user.role == "admin"
        pedido = service.cambiar_estado(
            pedido_id=pedido_id,
            estado_in=estado_in,
            usuario_id=current_user.id,
            es_admin=es_admin,
        )
        uow.commit()
        return pedido

@router.patch("/{pedido_id}/cancelar", response_model=PedidoRead)
def cancelar_pedido(
    pedido_id: int,
    current_user: Annotated[Usuario, Depends(get_current_active_user)],
):
    """
    Cancela un pedido propio en estado PENDIENTE (RN-03, RN-04).
    Devuelve 404 si no existe, 403 si es ajeno, y 400 si no está pendiente.
    """
    with PedidoUnitOfWork() as uow:
        service = PedidoService(uow)
        es_admin = current_user.role == "admin"
        pedido = service.cancelar_pedido(
            pedido_id=pedido_id,
            usuario_id=current_user.id,
            es_admin=es_admin,
        )
        uow.commit()
        return pedido