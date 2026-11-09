from sqlmodel import Session

from app.core.unit_of_work import UnitOfWork as BaseUnitOfWork
from app.modules.pedidos.repository import PedidoRepository
from app.modules.productos.repository import ProductoRepository


class PedidoUnitOfWork(BaseUnitOfWork):
    def __init__(self, session: Session | None = None) -> None:
        # Llama al __init__ del padre para que maneje la sesión (SessionLocal si es None)
        super().__init__(session)
        
        # Inicializa los repositorios específicos usando la sesión gestionada por el UoW
        self.pedidos = PedidoRepository(self._session)
        self.productos = ProductoRepository(self._session)