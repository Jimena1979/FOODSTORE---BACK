from datetime import UTC, datetime

from sqlalchemy.orm import selectinload
from sqlmodel import func, select

from app.core.base_repository import BaseRepository
from app.modules.pedidos.models import Pedido


class PedidoRepository(BaseRepository[Pedido]):
    def __init__(self, session) -> None:
        super().__init__(session, Pedido)

    def get_by_id_con_items(self, pedido_id: int) -> Pedido | None:
        return self.session.exec(
            select(Pedido)
            .options(selectinload(Pedido.items))
            .where(Pedido.id == pedido_id)
        ).first()

    def get_all_paginated(
        self,
        skip: int = 0,
        limit: int = 20,
        usuario_id: int | None = None,
        estado: str | None = None,
    ) -> tuple[list[Pedido], int]:
        estado_normalizado = estado.strip().upper() if estado and estado.strip() else None

        query = select(Pedido).options(selectinload(Pedido.items))

        if usuario_id is not None:
            query = query.where(Pedido.usuario_id == usuario_id)

        if estado_normalizado:
            query = query.where(Pedido.estado == estado_normalizado)

        condiciones = []
        if usuario_id is not None:
            condiciones.append(Pedido.usuario_id == usuario_id)
        if estado_normalizado:
            condiciones.append(Pedido.estado == estado_normalizado)

        count_query = select(func.count()).select_from(
            select(Pedido.id).where(*condiciones).subquery()
        )
        total = self.session.exec(count_query).one()

        query = query.order_by(Pedido.created_at.desc()).offset(skip).limit(limit)
        pedidos = self.session.exec(query).all()
        return list(pedidos), total

    def count_by_estado(self) -> dict[str, int]:
        estados = ["PENDIENTE", "EN_PREPARACION", "ENTREGADO", "CANCELADO"]
        conteo: dict[str, int] = {}
        for estado in estados:
            stmt = select(func.count(Pedido.id)).where(Pedido.estado == estado)
            conteo[estado.lower()] = self.session.exec(stmt).one()
        return conteo

    def get_resumen_estadisticas(self) -> dict:
        conteo_estados = self.count_by_estado()

        hoy_inicio = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        stmt_hoy = select(func.count(Pedido.id)).where(Pedido.created_at >= hoy_inicio)
        pedidos_hoy = self.session.exec(stmt_hoy).one()

        stmt_ingresos = select(func.sum(Pedido.total)).where(Pedido.estado == "ENTREGADO")
        ingresos = self.session.exec(stmt_ingresos).one() or 0.0

        return {
            "pendientes": conteo_estados.get("pendiente", 0),
            "en_preparacion": conteo_estados.get("en_preparacion", 0),
            "entregados": conteo_estados.get("entregado", 0),
            "cancelados": conteo_estados.get("cancelado", 0),
            "pedidos_hoy": pedidos_hoy,
            "ingresos_entregados": float(ingresos),
        }

    def create(self, pedido: Pedido) -> Pedido:
        return self.add(pedido)

    def update(self, pedido: Pedido) -> Pedido:
        self.session.add(pedido)
        self.session.flush()
        self.session.refresh(pedido)
        return pedido