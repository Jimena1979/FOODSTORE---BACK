from datetime import UTC, datetime

from sqlmodel import func, select

from app.core.base_repository import BaseRepository
from app.modules.pedidos.models import Pedido


class PedidoRepository(BaseRepository[Pedido]):
    def __init__(self, session) -> None:
        super().__init__(session, Pedido)

    def get_by_id_activo(self, id: int) -> Pedido | None:
        return self.session.exec(
            select(Pedido).where(Pedido.id == id)
        ).first()

    def get_all_paginated(
        self, skip: int = 0, limit: int = 20, usuario_id: int | None = None
    ) -> tuple[list[Pedido], int]:
        query = select(Pedido)
        
        if usuario_id is not None:
            query = query.where(Pedido.usuario_id == usuario_id)

        # Contar total sin paginación para los metadatos
        count_query = select(func.count()).select_from(query.subquery())
        total = self.session.exec(count_query).one()

        # Aplicar orden, paginación y ejecución
        query = query.order_by(Pedido.created_at.desc()).offset(skip).limit(limit)
        pedidos = self.session.exec(query).all()

        return list(pedidos), total

    def get_resumen_estadisticas(self) -> dict:
        estados = ["PENDIENTE", "EN_PREPARACION", "ENTREGADO", "CANCELADO"]
        conteo_estados = {}
        for estado in estados:
            stmt = select(func.count(Pedido.id)).where(Pedido.estado == estado)
            conteo_estados[estado.lower()] = self.session.exec(stmt).one()

        # Pedidos creados hoy
        hoy_inicio = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        stmt_hoy = select(func.count(Pedido.id)).where(Pedido.created_at >= hoy_inicio)
        pedidos_hoy = self.session.exec(stmt_hoy).one()

        # Ingresos totales de pedidos entregados
        stmt_ingresos = select(func.sum(Pedido.total)).where(Pedido.estado == "ENTREGADO")
        ingresos = self.session.exec(stmt_ingresos).one() or 0.0

        return {
            "pendientes": conteo_estados.get("pendiente", 0),
            "en_preparacion": conteo_estados.get("en_preparacion", 0),
            "entregados": conteo_estados.get("entregado", 0),
            "cancelados": conteo_estados.get("cancelado", 0),
            "pedidos_hoy": pedidos_hoy,
            "ingresos_entregados": ingresos,
        }