from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.deps import require_role
from app.modules.productos.schemas import (
    ProductoCreate,
    ProductoRead,
    ProductosPaginados,
    ProductoStockUpdate,
    ProductoUpdate,
)
from app.modules.productos.service import (
    CategoriaNoEncontrada,
    NombreDuplicado,
    ProductoNoEncontrado,
    ProductoService,
)
from app.modules.usuarios.schemas import UserPublic

router = APIRouter(prefix="/productos", tags=["Productos"])


def get_producto_service() -> ProductoService:
    return ProductoService()


@router.get("/", response_model=ProductosPaginados, status_code=status.HTTP_200_OK)
def listar_productos(
    service: Annotated[ProductoService, Depends(get_producto_service)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = None,
    categoria_id: int | None = None,
    disponible: bool | None = None,
):
    """Lista productos activos de forma paginada, con filtros opcionales de búsqueda, categoría y disponibilidad.

    Acceso: Público.
    """
    return service.listar_productos(
        skip=skip,
        limit=limit,
        search=search,
        categoria_id=categoria_id,
        disponible=disponible,
    )


@router.get("/{id}", response_model=ProductoRead, status_code=status.HTTP_200_OK)
def obtener_producto(
    id: int,
    service: Annotated[ProductoService, Depends(get_producto_service)],
):
    """Obtiene el detalle de un producto activo junto con su categoría.

    Acceso: Público.
    """
    try:
        return service.obtener_por_id(id)
    except ProductoNoEncontrado as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/", response_model=ProductoRead, status_code=status.HTTP_201_CREATED)
def crear_producto(
    data: ProductoCreate,
    _admin: Annotated[UserPublic, Depends(require_role(["admin"]))],
    service: Annotated[ProductoService, Depends(get_producto_service)],
):
    """Crea un nuevo producto asociado a un categoria_id.

    Acceso: Solo Admin.
    """
    try:
        return service.crear_producto(data)
    except CategoriaNoEncontrada as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except NombreDuplicado as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.put("/{id}", response_model=ProductoRead, status_code=status.HTTP_200_OK)
def actualizar_producto(
    id: int,
    data: ProductoUpdate,
    _admin: Annotated[UserPublic, Depends(require_role(["admin"]))],
    service: Annotated[ProductoService, Depends(get_producto_service)],
):
    """Actualiza de forma parcial los campos enviados de un producto existente.

    Acceso: Solo Admin.
    """
    try:
        return service.actualizar_producto(id, data)
    except (ProductoNoEncontrado, CategoriaNoEncontrada) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except NombreDuplicado as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.patch("/{id}/stock", response_model=ProductoRead, status_code=status.HTTP_200_OK)
def actualizar_stock_producto(
    id: int,
    data: ProductoStockUpdate,
    _admin: Annotated[UserPublic, Depends(require_role(["admin"]))],
    service: Annotated[ProductoService, Depends(get_producto_service)],
):
    """Actualiza el stock y la disponibilidad de un producto.

    Acceso: Solo Admin.
    """
    try:
        return service.actualizar_stock(id, data)
    except ProductoNoEncontrado as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def baja_logica_producto(
    id: int,
    _admin: Annotated[UserPublic, Depends(require_role(["admin"]))],
    service: Annotated[ProductoService, Depends(get_producto_service)],
):
    """Realiza la baja lógica de un producto (activo = False). Responde 204 sin

    cuerpo. Acceso: Solo Admin.
    """
    try:
        service.baja_logica(id)
    except ProductoNoEncontrado as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)