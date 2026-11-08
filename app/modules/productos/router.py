from fastapi import APIRouter, Depends, Query, Response, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.deps import require_role
from app.modules.productos.schemas import (
    ProductoCreate,
    ProductoRead,
    ProductosPaginados,
    ProductoStockUpdate,
    ProductoUpdate,
)
from app.modules.productos.service import ProductoService
from app.modules.productos.unit_of_work import ProductoUnitOfWork

router = APIRouter(prefix="/productos", tags=["Productos"])


def get_producto_service(
    session: Session = Depends(get_session),  # noqa: B008
) -> ProductoService: 
    uow = ProductoUnitOfWork(session)
    return ProductoService(uow)


@router.get("/", response_model=ProductosPaginados, status_code=status.HTTP_200_OK)
def listar_productos(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = None,
    categoria_id: int | None = None,
    disponible: bool | None = None,
    service: ProductoService = Depends(get_producto_service),  # noqa: B008
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
    service: ProductoService = Depends(get_producto_service),  # noqa: B008
):
    """Obtiene el detalle de un producto activo junto con su categoría.

    Acceso: Público.
    """
    return service.obtener_por_id(id)


@router.post("/", response_model=ProductoRead, status_code=status.HTTP_201_CREATED)
def crear_producto(
    data: ProductoCreate,
    service: ProductoService = Depends(get_producto_service),  # noqa: B008
    _=Depends(require_role(["admin"])),  # noqa: B008
):
    """Crea un nuevo producto asociado a un categoria_id.

    Acceso: Solo Admin.
    """
    return service.crear_producto(data)


@router.put("/{id}", response_model=ProductoRead, status_code=status.HTTP_200_OK)
def actualizar_producto(
    id: int,
    data: ProductoUpdate,
    service: ProductoService = Depends(get_producto_service),  # noqa: B008
    _=Depends(require_role(["admin"])),  # noqa: B008
):
    """Actualiza de forma parcial los campos enviados de un producto existente.

    Acceso: Solo Admin.
    """
    return service.actualizar_producto(id, data)


@router.patch("/{id}/stock", response_model=ProductoRead, status_code=status.HTTP_200_OK)
def actualizar_stock_producto(
    id: int,
    data: ProductoStockUpdate,
    service: ProductoService = Depends(get_producto_service),  # noqa: B008
    _=Depends(require_role(["admin"])),  # noqa: B008
):
    """Actualiza el stock y la disponibilidad de un producto.

    Acceso: Solo Admin.
    """
    return service.actualizar_stock(id, data)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def baja_logica_producto(
    id: int,
    service: ProductoService = Depends(get_producto_service),  # noqa: B008
    _=Depends(require_role(["admin"])),  # noqa: B008
):
    """Realiza la baja lógica de un producto (activo = False). Responde 204 sin

    cuerpo. Acceso: Solo Admin.
    """
    service.baja_logica(id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)