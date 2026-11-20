from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_current_active_user, require_role
from app.modules.pedidos.schemas import (
    CambioEstado,
    PedidoCreate,
    PedidoRead,
    PedidosPaginados,
    ResumenPedidos,
)
from app.modules.pedidos.service import (
    PedidoAjeno,
    PedidoNoEncontrado,
    PedidoService,
    ProductoNoDisponible,
    ProductoNoEncontrado,
    ProductoRepetido,
    StockInsuficiente,
    TransicionInvalida,
)
from app.modules.usuarios.schemas import UserPublic

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


def get_pedido_service() -> PedidoService:
    return PedidoService()


@router.post("", response_model=PedidoRead, status_code=status.HTTP_201_CREATED)
def crear_pedido(
    data: PedidoCreate,
    current_user: Annotated[UserPublic, Depends(get_current_active_user)],
    service: Annotated[PedidoService, Depends(get_pedido_service)],
):
    try:
        return service.crear_pedido(usuario_id=current_user.id, data=data)
    except ProductoNoEncontrado as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (ProductoNoDisponible, StockInsuficiente, ProductoRepetido) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=PedidosPaginados)
def listar_pedidos(
    current_user: Annotated[UserPublic, Depends(get_current_active_user)],
    service: Annotated[PedidoService, Depends(get_pedido_service)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    estado: Annotated[str | None, Query()] = None,
    solo_mios: Annotated[bool, Query()] = False,
):
    es_admin = current_user.role == "admin"
    usuario_id_filtro = None if (es_admin and not solo_mios) else current_user.id
    return service.listar_pedidos(
        skip=skip,
        limit=limit,
        usuario_id=usuario_id_filtro,
        estado=estado,
    )


@router.get("/resumen", response_model=ResumenPedidos)
def obtener_resumen_pedidos(
    _admin: Annotated[UserPublic, Depends(require_role(["admin"]))],
    service: Annotated[PedidoService, Depends(get_pedido_service)],
):
    return service.obtener_resumen()


@router.get("/{pedido_id}", response_model=PedidoRead)
def obtener_pedido(
    pedido_id: int,
    current_user: Annotated[UserPublic, Depends(get_current_active_user)],
    service: Annotated[PedidoService, Depends(get_pedido_service)],
):
    try:
        es_admin = current_user.role == "admin"
        return service.obtener_pedido_por_id(
            pedido_id=pedido_id,
            usuario_id=current_user.id,
            es_admin=es_admin,
        )
    except PedidoNoEncontrado as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PedidoAjeno as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.patch("/{pedido_id}/estado", response_model=PedidoRead)
def cambiar_estado_pedido(
    pedido_id: int,
    estado_in: CambioEstado,
    _admin: Annotated[UserPublic, Depends(require_role(["admin"]))],
    current_user: Annotated[UserPublic, Depends(get_current_active_user)],
    service: Annotated[PedidoService, Depends(get_pedido_service)],
):
    try:
        return service.cambiar_estado(
            pedido_id=pedido_id,
            estado_in=estado_in,
            usuario_id=current_user.id,
            es_admin=True,
        )
    except PedidoNoEncontrado as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TransicionInvalida as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/{pedido_id}/cancelar", response_model=PedidoRead)
def cancelar_pedido(
    pedido_id: int,
    current_user: Annotated[UserPublic, Depends(get_current_active_user)],
    service: Annotated[PedidoService, Depends(get_pedido_service)],
):
    try:
        es_admin = current_user.role == "admin"
        return service.cancelar_pedido(
            pedido_id=pedido_id,
            usuario_id=current_user.id,
            es_admin=es_admin,
        )
    except PedidoNoEncontrado as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PedidoAjeno as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TransicionInvalida as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc