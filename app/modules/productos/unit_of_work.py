from sqlmodel import Session

from app.categoria.repository import CategoriaRepository
from app.core.unit_of_work import UnitOfWork as BaseUnitOfWork
from app.ingrediente.repository import IngredienteRepository
from app.producto.repository import ProductoRepository


class ProductoUnitOfWork(BaseUnitOfWork):
    """
    UoW específico del módulo Productos.
    Expone los repositorios que el servicio de productos necesita coordinar
    bajo una misma transacción atómica.
    """

    def __init__(self, session: Session | None = None) -> None:
        super().__init__(session)
        self.productos = ProductoRepository(self._session)
        self.categorias = CategoriaRepository(self._session)
        self.ingredientes = IngredienteRepository(self._session)