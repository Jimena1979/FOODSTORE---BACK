from collections.abc import Sequence

from sqlmodel import func, select

from app.core.base_repository import BaseRepository
from app.modules.categorias.models import Categoria


class CategoriaRepository(BaseRepository[Categoria]):
    def __init__(self, session) -> None:
        super().__init__(session, Categoria)

    def get_by_nombre(self, nombre: str) -> Categoria | None:
        nombre_normalizado = nombre.strip().lower()
        statement = select(self.model).where(
            func.lower(self.model.nombre) == nombre_normalizado
        )
        instance = self.session.exec(statement).first()
        if instance:
            self.session.expunge(instance)
        return instance

    def get_all_paginated(
        self, skip: int = 0, limit: int = 20, activo: bool | None = True
    ) -> Sequence[Categoria]:
        """Obtiene categorías paginadas filtrando opcionalmente por su estado activo."""
        query = select(Categoria)
        if activo is not None:
            query = query.where(Categoria.activo == activo)

        categorias = self.session.exec(query.offset(skip).limit(limit)).all()
        for cat in categorias:
            self.session.expunge(cat)
        return categorias