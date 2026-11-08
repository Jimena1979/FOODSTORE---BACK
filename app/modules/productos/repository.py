from sqlmodel import col, select

from app.core.base_repository import BaseRepository
from app.modules.productos.models import Producto


class ProductoRepository(BaseRepository[Producto]):
    def __init__(self, session) -> None:
        super().__init__(session, Producto)

    def search(
        self,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
        categoria_id: int | None = None,
        disponible: bool | None = None,
        solo_activos: bool = True
    ) -> tuple[list[Producto], int]:
        query = select(Producto)
        count_query = select(Producto)

        # Por defecto los listados públicos devuelven solo registros activos
        if solo_activos:
            query = query.where(Producto.activo == True)
            count_query = count_query.where(Producto.activo == True)

        # Búsqueda por nombre (insensible a mayúsculas/minúsculas con ilike)
        if search:
            search_filter = col(Producto.nombre).ilike(f"%{search}%")
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        # Filtro por categoría (relación 1:N directa)
        if categoria_id is not None:
            query = query.where(Producto.categoria_id == categoria_id)
            count_query = count_query.where(Producto.categoria_id == categoria_id)

        # Filtro por disponibilidad
        if disponible is not None:
            query = query.where(Producto.disponible == disponible)
            count_query = count_query.where(Producto.disponible == disponible)

        # Calcular el total para la paginación e implementar offset/limit
        total = len(self.session.exec(count_query).all())
        query = query.offset(skip).limit(limit)
        items = list(self.session.exec(query).all())

        return items, total