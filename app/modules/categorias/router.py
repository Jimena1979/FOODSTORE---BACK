from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.unit_of_work import UnitOfWork, get_uow
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
    uow: Annotated[UnitOfWork, Depends(get_uow)] = None,
) -> list[CategoriaRead]:
    """Lista las categorías activas de forma paginada."""
    with uow:
        service = CategoriaService(uow)
        return service.listar_activas(skip=skip, limit=limit)


@router.get("/{categoria_id}", response_model=CategoriaRead, status_code=status.HTTP_200_OK)
def obtener_categoria(
    categoria_id: int,
    uow: Annotated[UnitOfWork, Depends(get_uow)] = None,
) -> CategoriaRead:
    """Obtiene una categoría activa por su ID (devuelve 404 si no existe o está inactiva)."""
    with uow:
        service = CategoriaService(uow)
        return service.obtener_por_id(categoria_id)


@router.post("/", response_model=CategoriaRead, status_code=status.HTTP_201_CREATED)
def crear_categoria(
    data: CategoriaCreate,
    uow: Annotated[UnitOfWork, Depends(get_uow)] = None,
    # _admin: Annotated[Any, Depends(require_role(["admin"]))] = None, # Descomentar si solo los admin pueden crear
) -> CategoriaRead:
    """Crea una nueva categoría (devuelve 409 si el nombre ya existe)."""
    with uow:
        service = CategoriaService(uow)
        categoria = service.crear(data)
        uow.commit()
        return categoria


@router.put("/{categoria_id}", response_model=CategoriaRead, status_code=status.HTTP_200_OK)
def actualizar_categoria(
    categoria_id: int,
    data: CategoriaUpdate,
    uow: Annotated[UnitOfWork, Depends(get_uow)] = None,
) -> CategoriaRead:
    """Actualiza parcialmente una categoría existente (excluyendo el campo activo)."""
    with uow:
        service = CategoriaService(uow)
        categoria = service.actualizar(categoria_id, data)
        uow.commit()
        return categoria


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def baja_logica_categoria(
    categoria_id: int,
    uow: Annotated[UnitOfWork, Depends(get_uow)] = None,
) -> None:
    """Realiza la baja lógica de una categoría cambiando su estado activo a false."""
    with uow:
        service = CategoriaService(uow)
        service.baja_logica(categoria_id)
        uow.commit()