from app.modules.categorias.models import Categoria
from app.modules.categorias.schemas import (
    CategoriaCreate,
    CategoriaRead,
    CategoriaUpdate,
)
from app.modules.categorias.unit_of_work import CategoriaUnitOfWork


class CategoriaNoEncontrada(Exception):
    pass


class NombreDuplicado(Exception):
    pass


class CategoriaService:
    def __init__(self, uow: CategoriaUnitOfWork | None = None) -> None:
        self.uow = uow or CategoriaUnitOfWork()

    def listar_activas(self, skip: int = 0, limit: int = 20) -> list[CategoriaRead]:
        with self.uow as uow:
            categorias = uow.categorias.get_all_paginated(
                skip=skip, limit=limit, activo=True
            )
            return [CategoriaRead.model_validate(c) for c in categorias]

    def obtener_por_id(self, categoria_id: int) -> CategoriaRead:
        with self.uow as uow:
            categoria = uow.categorias.get_by_id(categoria_id)
            if not categoria or not categoria.activo:
                raise CategoriaNoEncontrada("Categoría no encontrada")
            return CategoriaRead.model_validate(categoria)

    def crear(self, data: CategoriaCreate) -> CategoriaRead:
        with self.uow as uow:
            nombre_limpio = data.nombre.strip()
            existente = uow.categorias.get_by_nombre(nombre_limpio)
            if existente:
                raise NombreDuplicado("El nombre de la categoría ya existe")

            payload = data.model_dump()
            payload["nombre"] = nombre_limpio
            if isinstance(payload.get("descripcion"), str):
                payload["descripcion"] = payload["descripcion"].strip()

            nueva = Categoria(**payload)
            uow.categorias.add(nueva)
            return CategoriaRead.model_validate(nueva)

    def actualizar(self, categoria_id: int, data: CategoriaUpdate) -> CategoriaRead:
        with self.uow as uow:
            categoria = uow.categorias.get_by_id(categoria_id)
            if not categoria or not categoria.activo:
                raise CategoriaNoEncontrada("Categoría no encontrada")

            datos_update = data.model_dump(exclude_unset=True)
            if "nombre" in datos_update and datos_update["nombre"] is not None:
                nuevo_nombre = datos_update["nombre"].strip()
                datos_update["nombre"] = nuevo_nombre
                if nuevo_nombre.lower() != categoria.nombre.strip().lower():
                    duplicada = uow.categorias.get_by_nombre(nuevo_nombre)
                    if duplicada:
                        raise NombreDuplicado("El nombre de la categoría ya existe")

            if isinstance(datos_update.get("descripcion"), str):
                datos_update["descripcion"] = datos_update["descripcion"].strip()

            for key, value in datos_update.items():
                setattr(categoria, key, value)

            uow.categorias.add(categoria)
            return CategoriaRead.model_validate(categoria)

    def baja_logica(self, categoria_id: int) -> None:
        with self.uow as uow:
            categoria = uow.categorias.get_by_id(categoria_id)
            if not categoria or not categoria.activo:
                raise CategoriaNoEncontrada("Categoría no encontrada")

            categoria.activo = False
            uow.categorias.add(categoria)