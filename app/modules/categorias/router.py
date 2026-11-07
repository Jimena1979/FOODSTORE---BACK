
from typing import Annotated

from app.core.dependencies import (
    get_categoria_service,  # O como este nombrado en el proyecto
)
from fastapi import APIRouter, Depends, Query, status

from app.modules.categorias.schemas import (
    CategoriaCreate,
    CategoriaRead,
    CategoriaUpdate,
)
from app.modules.categorias.service import CategoriaService

router = APIRouter(prefix="/categorias", tags=["Categorías"])


@router.get("/", response_model=list[CategoriaRead], status_code=status.HTTP_200_OK)
def listar_categorias(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    service: Annotated[CategoriaService, Depends(get_categoria_service)] = ...,
) -> list[CategoriaRead]:
    """Lista las categorías activas de forma paginada."""
    return service.listar_activas(skip=skip, limit=limit)


@router.get("/{categoria_id}", response_model=CategoriaRead, status_code=status.HTTP_200_OK)
def obtener_categoria(
    categoria_id: int,
    service: Annotated[CategoriaService, Depends(get_categoria_service)] = ...,
) -> CategoriaRead:
    """Obtiene una categoría activa por su ID (devuelve 404 si no existe o está inactiva)."""
    return service.obtener_por_id(categoria_id)


@router.post("/", response_model=CategoriaRead, status_code=status.HTTP_201_CREATED)
def crear_categoria(
    data: CategoriaCreate,
    service: Annotated[CategoriaService, Depends(get_categoria_service)] = ...,
) -> CategoriaRead:
    """Crea una nueva categoría (devuelve 409 si el nombre ya existe)."""
    return service.crear(data)


@router.put("/{categoria_id}", response_model=CategoriaRead, status_code=status.HTTP_200_OK)
def actualizar_categoria(
    categoria_id: int,
    data: CategoriaUpdate,
    service: Annotated[CategoriaService, Depends(get_categoria_service)] = ...,
) -> CategoriaRead:
    """Actualiza parcialmente una categoría existente (excluyendo el campo activo)."""
    return service.actualizar(categoria_id, data)


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def baja_logica_categoria(
    categoria_id: int,
    service: Annotated[CategoriaService, Depends(get_categoria_service)] = ...,
) -> None:
    """Realiza la baja lógica de una categoría cambiando su estado activo a false."""
    service.baja_logica(categoria_id)