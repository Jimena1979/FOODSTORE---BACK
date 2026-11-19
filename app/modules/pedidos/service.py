from datetime import UTC, datetime

from app.modules.pedidos.models import DetallePedido, Pedido
from app.modules.pedidos.schemas import (
    CambioEstado,
    PedidoCreate,
    PedidoRead,
    PedidosPaginados,
    ResumenPedidos,
)
from app.modules.pedidos.unit_of_work import PedidoUnitOfWork


class PedidoNoEncontrado(Exception):
    pass


class ProductoNoEncontrado(Exception):
    pass


class ProductoNoDisponible(Exception):
    pass


class StockInsuficiente(Exception):
    pass


class ProductoRepetido(Exception):
    pass


class PedidoAjeno(Exception):
    pass


class TransicionInvalida(Exception):
    pass


TRANSICIONES_VALIDAS: dict[str, set[str]] = {
    "PENDIENTE": {"EN_PREPARACION", "CANCELADO"},
    "EN_PREPARACION": {"ENTREGADO", "CANCELADO"},
    "ENTREGADO": set(),
    "CANCELADO": set(),
}


class PedidoService:
    def __init__(self, uow: PedidoUnitOfWork | None = None) -> None:
        self.uow = uow or PedidoUnitOfWork()

    def crear_pedido(self, usuario_id: int, data: PedidoCreate) -> PedidoRead:
        with self.uow as uow:
            productos_vistos: set[int] = set()
            for item_data in data.items:
                if item_data.producto_id in productos_vistos:
                    raise ProductoRepetido(
                        f"El producto con id {item_data.producto_id} está repetido en el pedido."
                    )
                productos_vistos.add(item_data.producto_id)

            nuevo_pedido = Pedido(
                usuario_id=usuario_id,
                estado="PENDIENTE",
                forma_pago=data.forma_pago,
                direccion_entrega=data.direccion_entrega,
                notas=data.notas,
                total=0.0,
            )
            uow.pedidos.create(nuevo_pedido)

            total_pedido = 0.0

            for item_data in data.items:
                producto = uow.productos.get_by_id(item_data.producto_id)
                if not producto or not producto.activo:
                    raise ProductoNoEncontrado(
                        f"Producto con id {item_data.producto_id} no encontrado o inactivo."
                    )

                if not producto.disponible:
                    raise ProductoNoDisponible(
                        f"El producto '{producto.nombre}' no se encuentra disponible."
                    )

                if producto.stock < item_data.cantidad:
                    raise StockInsuficiente(
                        f"Stock insuficiente para '{producto.nombre}'. Stock actual: {producto.stock}"
                    )

                producto.stock -= item_data.cantidad
                uow.productos.add(producto)

                subtotal = float(producto.precio_base) * item_data.cantidad
                total_pedido += subtotal

                detalle = DetallePedido(
                    pedido_id=nuevo_pedido.id,
                    producto_id=producto.id,
                    cantidad=item_data.cantidad,
                    nombre_producto=producto.nombre,
                    precio_unitario=float(producto.precio_base),
                    subtotal=subtotal,
                )
                uow._session.add(detalle)

            nuevo_pedido.total = total_pedido
            uow.pedidos.update(nuevo_pedido)

            pedido_completo = uow.pedidos.get_by_id_con_items(nuevo_pedido.id)
            return PedidoRead.model_validate(pedido_completo)

    def obtener_pedido_por_id(
        self, pedido_id: int, usuario_id: int, es_admin: bool
    ) -> PedidoRead:
        with self.uow as uow:
            pedido = uow.pedidos.get_by_id_con_items(pedido_id)
            if not pedido:
                raise PedidoNoEncontrado("Pedido no encontrado.")

            if not es_admin and pedido.usuario_id != usuario_id:
                raise PedidoAjeno("No tienes permisos para ver este pedido.")

            return PedidoRead.model_validate(pedido)

    def listar_pedidos(
        self,
        skip: int = 0,
        limit: int = 20,
        usuario_id: int | None = None,
        estado: str | None = None,
    ) -> PedidosPaginados:
        with self.uow as uow:
            pedidos, total = uow.pedidos.get_all_paginated(
                skip=skip,
                limit=limit,
                usuario_id=usuario_id,
                estado=estado,
            )
            return PedidosPaginados(
                total=total,
                items=[PedidoRead.model_validate(p) for p in pedidos],
            )

    def cambiar_estado(
        self, pedido_id: int, estado_in: CambioEstado, usuario_id: int, es_admin: bool
    ) -> PedidoRead:
        with self.uow as uow:
            pedido = uow.pedidos.get_by_id_con_items(pedido_id)
            if not pedido:
                raise PedidoNoEncontrado("Pedido no encontrado.")

            nuevo_estado = estado_in.estado

            if not es_admin:
                if pedido.usuario_id != usuario_id:
                    raise PedidoAjeno("No autorizado.")
                if nuevo_estado != "CANCELADO" or pedido.estado != "PENDIENTE":
                    raise TransicionInvalida(
                        "Los clientes solo pueden cancelar pedidos que se encuentren en estado PENDIENTE."
                    )
            else:
                permitidos = TRANSICIONES_VALIDAS.get(pedido.estado, set())
                if nuevo_estado not in permitidos:
                    raise TransicionInvalida(
                        f"Transición de '{pedido.estado}' a '{nuevo_estado}' no permitida."
                    )

            if nuevo_estado == "CANCELADO" and pedido.estado != "CANCELADO":
                for detalle in pedido.items:
                    producto = uow.productos.get_by_id(detalle.producto_id)
                    if producto:
                        producto.stock += detalle.cantidad
                        uow.productos.add(producto)

            pedido.estado = nuevo_estado
            pedido.updated_at = datetime.now(UTC)
            uow.pedidos.update(pedido)

            pedido_actualizado = uow.pedidos.get_by_id_con_items(pedido.id)
            return PedidoRead.model_validate(pedido_actualizado)

    def obtener_resumen(self) -> ResumenPedidos:
        with self.uow as uow:
            resumen = uow.pedidos.get_resumen_estadisticas()
            return ResumenPedidos.model_validate(resumen)

    def cancelar_pedido(
        self, pedido_id: int, usuario_id: int, es_admin: bool
    ) -> PedidoRead:
        with self.uow as uow:
            pedido = uow.pedidos.get_by_id_con_items(pedido_id)
            if not pedido:
                raise PedidoNoEncontrado("Pedido no encontrado.")

            if not es_admin and pedido.usuario_id != usuario_id:
                raise PedidoAjeno("No tienes permisos para cancelar un pedido ajeno.")

            if pedido.estado != "PENDIENTE":
                raise TransicionInvalida(
                    "Solo se pueden cancelar pedidos que se encuentren en estado PENDIENTE."
                )

            for detalle in pedido.items:
                producto = uow.productos.get_by_id(detalle.producto_id)
                if producto:
                    producto.stock += detalle.cantidad
                    uow.productos.add(producto)

            pedido.estado = "CANCELADO"
            pedido.updated_at = datetime.now(UTC)
            uow.pedidos.update(pedido)

            pedido_cancelado = uow.pedidos.get_by_id_con_items(pedido.id)
            return PedidoRead.model_validate(pedido_cancelado)
