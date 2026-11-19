from typing import Self

from sqlmodel import Session

from app.core.database import SessionLocal
from app.core.unit_of_work import UnitOfWork as BaseUnitOfWork
from app.modules.categorias.repository import CategoriaRepository
from app.modules.productos.repository import ProductoRepository


class CategoriaUnitOfWork(BaseUnitOfWork):
    """
    UoW específico del módulo Categorías.
    Coordina los repositorios necesarios para las operaciones de categoría
    y su relación con productos dentro de una misma transacción atómica.
    """

    def __init__(self, session_factory=None, session: Session | None = None) -> None:
        if session is not None:
            resolved_session = session
        elif session_factory is not None:
            created = session_factory()
            resolved_session = created() if callable(created) and not isinstance(created, Session) else created
        else:
            created = SessionLocal()
            resolved_session = created() if callable(created) and not isinstance(created, Session) else created

        super().__init__(session=resolved_session)
        self.categorias = CategoriaRepository(self._session)
        self.productos = ProductoRepository(self._session)

    def __enter__(self) -> Self:
        super().__enter__()
        self.categorias = CategoriaRepository(self._session)
        self.productos = ProductoRepository(self._session)
        return self