from sqlmodel import Session

from app.core.unit_of_work import UnitOfWork as BaseUnitOfWork
from app.modules.categorias.repository import CategoriaRepository
from app.modules.productos.repository import ProductoRepository


class ProductoUnitOfWork(BaseUnitOfWork):
    """
    UoW específico del módulo Productos.
    Expone los repositorios de productos y categorías para coordinar
    las validaciones y operaciones bajo una misma transacción atómica.
    """

    def __init__(self, session: Session | None = None) -> None:
        super().__init__(session)
        self.productos = ProductoRepository(self._session)
        self.categorias = CategoriaRepository(self._session)