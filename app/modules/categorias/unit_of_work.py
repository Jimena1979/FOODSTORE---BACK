from typing import Self

from app.categoria.repository import CategoriaRepository
from app.producto.repository import ProductoRepository
from sqlmodel import Session

from app.core.database import engine
from app.core.unit_of_work import UnitOfWork as BaseUnitOfWork


class CategoriaUnitOfWork(BaseUnitOfWork):
    """
    UoW específico del módulo Categorías.
    Coordina los repositorios necesarios para las operaciones de categoría
    y su relación con productos dentro de una misma transacción atómica.
    """

    def __init__(self, session_factory=None) -> None:
        # Si no pasan una fábrica, usamos una lambda que crea la sesión contra el engine
        super().__init__(session_factory or (lambda: Session(engine)))
        self.categorias: CategoriaRepository | None = None
        self.productos: ProductoRepository | None = None

    def __enter__(self) -> Self:
        # Ejecuta el __enter__ del BaseUnitOfWork (crea self._session y maneja la transacción)
        super().__enter__()
        
        # Inicializamos los repositorios con la sesión activa de esta transacción
        self.categorias = CategoriaRepository(self._session)
        self.productos = ProductoRepository(self._session)
        
        return self