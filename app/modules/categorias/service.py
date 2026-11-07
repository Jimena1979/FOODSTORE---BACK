
from fastapi import HTTPException, status

from app.core.unit_of_work import UnitOfWork
from app.modules.categorias.models import Categoria
from app.modules.categorias.schemas import (
    CategoriaCreate,
    CategoriaRead,
    CategoriaUpdate,
)


class CategoriaService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def listar_activas(self, skip: int = 0, limit: int = 20) -> list[CategoriaRead]:
        """Lista las categorías activas utilizando el repositorio."""
        with self.uow as uow:
            categorias = uow.categorias.get_all_paginated(skip=skip, limit=limit, activo=True)
            return [CategoriaRead.model_validate(c) for c in categorias]

    def obtener_por_id(self, categoria_id: int) -> CategoriaRead:
        with self.uow as uow:
            categoria = uow.categorias.get_by_id(categoria_id)
            if not categoria or not categoria.activo:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Categoría no encontrada",
                )
            return CategoriaRead.model_validate(categoria)

    def crear(self, data: CategoriaCreate) -> CategoriaRead:
        with self.uow as uow:
            existente = uow.categorias.get_by_nombre(data.nombre.lower())
            if existente:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="El nombre de la categoría ya existe",
                )
            nueva = Categoria(**data.model_dump())
            uow.categorias.add(nueva)
            uow._session.flush()
            uow._session.refresh(nueva)
            return CategoriaRead.model_validate(nueva)

    def actualizar(self, categoria_id: int, data: CategoriaUpdate) -> CategoriaRead:
        with self.uow as uow:
            categoria = uow.categorias.get_by_id(categoria_id)
            if not categoria or not categoria.activo:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Categoría no encontrada",
                )
            
            if data.nombre is not None and data.nombre.lower() != categoria.nombre.lower():
                duplicada = uow.categorias.get_by_nombre(data.nombre.lower())
                if duplicada:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="El nombre de la categoría ya existe",
                    )

            datos_update = data.model_dump(exclude_unset=True)
            for key, value in datos_update.items():
                setattr(categoria, key, value)
            
            uow._session.add(categoria)
            uow._session.flush()
            uow._session.refresh(categoria)
            return CategoriaRead.model_validate(categoria)

    def baja_logica(self, categoria_id: int) -> None:
        with self.uow as uow:
            categoria = uow.categorias.get_by_id(categoria_id)
            if not categoria or not categoria.activo:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Categoría no encontrada",
                )
            categoria.activo = False
            uow._session.add(categoria)
            uow._session.flush()