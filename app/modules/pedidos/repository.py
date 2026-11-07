from app.core.repository import BaseRepository
from sqlmodel import Session, select

from app.pedido.models import Pedido


class PedidoRepository(BaseRepository[Pedido]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Pedido)

    def get_by_id_activo(self, id: int) -> Pedido | None:
        return self.session.exec(
            select(Pedido).where(Pedido.id == id, Pedido.activo == True)
        ).first()

    def get_all_paginated(self, skip: int = 0, limit: int = 20, activo: bool | None = True) -> list[Pedido]:
        query = select(Pedido)
        if activo is not None:
            query = query.where(Pedido.activo == activo)
        return list(self.session.exec(query.offset(skip).limit(limit)).all())