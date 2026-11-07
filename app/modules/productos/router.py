from fastapi import APIRouter, Query, status

from app.producto import service as producto_service
from app.producto.schemas import (
    ProductoCreate,
    ProductoRead,
    ProductoStockResponse,
    ProductoUpdate,
)

router = APIRouter(prefix="/productos", tags=["Productos"])


@router.post("/", response_model=ProductoRead, status_code=status.HTTP_201_CREATED)
def alta_producto(producto: ProductoCreate):
    """Registra un nuevo producto básico en la base de datos."""
    return producto_service.crear(producto)


@router.get("/", response_model=list[ProductoRead], status_code=status.HTTP_200_OK)
def listar_productos(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, le=100),
    activo: bool | None = None,
):
    """Devuelve una lista paginada de productos con filtro opcional."""
    return producto_service.obtener_todos(skip, limit, activo)


@router.get("/relaciones", status_code=status.HTTP_200_OK)
def obtener_todas_las_relaciones():
    """Endpoint para listar todas las relaciones de categorías existentes (GET)."""
    return producto_service.listar_relaciones()


@router.get("/relaciones/ingredientes", status_code=status.HTTP_200_OK)
def obtener_relaciones_ingredientes():
    """Endpoint para listar todas las relaciones de ingredientes existentes (GET)."""
    return producto_service.listar_relaciones_ingredientes()


@router.get("/{id}", response_model=ProductoRead, status_code=status.HTTP_200_OK)
def detalle_producto(id: int):
    """Obtiene los datos detallados de un producto específico según su ID."""
    return producto_service.obtener_por_id(id)


@router.put("/{id}", response_model=ProductoRead, status_code=status.HTTP_200_OK)
def actualizar_producto(id: int, producto: ProductoUpdate):
    """Actualiza los datos de un producto existente."""
    return producto_service.actualizar_total(id, producto)


@router.post("/{producto_id}/categorias/{categoria_id}", status_code=status.HTTP_201_CREATED)
def asignar_categoria(producto_id: int, categoria_id: int):
    """Asocia una categoría a un producto mediante la tabla intermedia."""
    return producto_service.vincular_categoria(producto_id, categoria_id)


@router.delete("/{producto_id}/categorias/{categoria_id}", status_code=status.HTTP_200_OK)
def desvincular_producto_de_categoria(producto_id: int, categoria_id: int):
    """Endpoint para desvincular un producto de una categoría (DELETE)."""
    return producto_service.desvincular_categoria(producto_id, categoria_id)


@router.post("/{producto_id}/ingredientes/{ingrediente_id}", status_code=status.HTTP_201_CREATED)
def asignar_ingrediente(producto_id: int, ingrediente_id: int):
    """Asocia un ingrediente a un producto mediante la tabla intermedia."""
    return producto_service.vincular_ingrediente(producto_id, ingrediente_id)


@router.delete("/{producto_id}/ingredientes/{ingrediente_id}", status_code=status.HTTP_200_OK)
def desvincular_ingrediente_de_producto(producto_id: int, ingrediente_id: int):
    """Endpoint para desvincular un ingrediente de un producto (DELETE)."""
    return producto_service.desvincular_ingrediente(producto_id, ingrediente_id)


@router.put("/{id}/desactivar", response_model=ProductoRead, status_code=status.HTTP_200_OK)
def borrado_logico_put(id: int):
    """Realiza una baja lógica del producto cambiando su estado 'activo' a False (PUT)."""
    return producto_service.desactivar(id)


@router.delete("/{id}", response_model=ProductoRead, status_code=status.HTTP_200_OK)
def eliminar_producto(id: int):
    """Realiza una baja lógica del producto mediante el verbo DELETE."""
    return producto_service.desactivar(id)


@router.get("/{id}/stock", response_model=ProductoStockResponse, status_code=status.HTTP_200_OK)
def consultar_stock(id: int):
    """Consulta el estado actual del inventario de un producto."""
    return producto_service.obtener_estado_stock(id)