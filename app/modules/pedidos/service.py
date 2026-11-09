from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.modules.pedidos.models import DetallePedido, Pedido
from app.modules.pedidos.repository import PedidoRepository
from app.modules.pedidos.schemas import CambioEstado, PedidoCreate
from app.modules.productos.repository import ProductoRepository


class PedidoService:
    def __init__(self, session):
        self.session = session
        self.pedido_repo = PedidoRepository(session)
        self.producto_repo = ProductoRepository(session)

    def crear_pedido(self, usuario_id: int, data: PedidoCreate) -> Pedido:
        detalles_pedido: list[DetallePedido] = []
        total_pedido = 0.0

        # 1. Validar y procesar cada ítem del pedido (RN-01, RN-05)
        for item_data in data.items:
            producto = self.producto_repo.get_by_id(item_data.producto_id)
            if not producto:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Producto con id {item_data.producto_id} no encontrado."
                )

            # Validar reglas de venta del producto (RN-01)
            if not producto.activo or not producto.disponible:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El producto '{producto.nombre}' no se encuentra activo o disponible."
                )

            if producto.stock < item_data.cantidad:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Stock insuficiente para el producto '{producto.nombre}'. Stock actual: {producto.stock}"
                )

            # Descontar stock (RN-01)
            producto.stock -= item_data.cantidad
            self.session.add(producto)

            # Copia inmutable de datos (Snapshot - RN-05)
            subtotal = producto.precio_base * item_data.cantidad
            total_pedido += subtotal

            detalle = DetallePedido(
                producto_id=producto.id,
                cantidad=item_data.cantidad,
                nombre_producto=producto.nombre,
                precio_unitario=producto.precio_base,
                subtotal=subtotal
            )
            detalles_pedido.append(detalle)

        # 2. Crear la entidad Pedido
        nuevo_pedido = Pedido(
            usuario_id=usuario_id,
            estado="PENDIENTE",
            forma_pago=data.forma_pago,
            direccion_entrega=data.direccion_entrega,
            notas=data.notas,
            total=total_pedido,
            items=detalles_pedido
        )

        # 3. Persistir usando el repositorio (el commit lo maneja el Unit of Work)
        return self.pedido_repo.create(nuevo_pedido)

    def obtener_pedido_por_id(self, pedido_id: int, usuario_id: int | None = None, es_admin: bool = False) -> Pedido:
        pedido = self.pedido_repo.get_by_id(pedido_id)
        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido no encontrado."
            )

        # Si no es admin, verificar que el pedido pertenezca al usuario autenticado
        if not es_admin and pedido.usuario_id != usuario_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para ver este pedido."
            )

        return pedido

    def listar_pedidos(self, skip: int, limit: int, usuario_id: int | None = None) -> tuple[list[Pedido], int]:
        return self.pedido_repo.get_all_paginated(skip=skip, limit=limit, usuario_id=usuario_id)

    def cambiar_estado(self, pedido_id: int, estado_in: CambioEstado, usuario_id: int, es_admin: bool) -> Pedido:
        pedido = self.pedido_repo.get_by_id(pedido_id)
        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido no encontrado."
            )

        nuevo_estado = estado_in.estado

        # Control de permisos y reglas de transición (RN-02, RN-03, RN-04)
        if not es_admin:
            # El cliente solo puede cancelar y únicamente si está PENDIENTE (RN-04)
            if pedido.usuario_id != usuario_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado.")
            if nuevo_estado != "CANCELADO" or pedido.estado != "PENDIENTE":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Los clientes solo pueden cancelar pedidos que se encuentren en estado PENDIENTE."
                )
        else:
            # Validaciones de transiciones permitidas para admin (RN-02)
            if pedido.estado in ["ENTREGADO", "CANCELADO"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El pedido ya se encuentra en un estado terminal ({pedido.estado}) y no puede modificarse."
                )
            
            if pedido.estado == "PENDIENTE" and nuevo_estado not in ["EN_PREPARACION", "CANCELADO"]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transición de estado no permitida.")
            
            if pedido.estado == "EN_PREPARACION" and nuevo_estado not in ["ENTREGADO", "CANCELADO"]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transición de estado no permitida.")

        # Si pasa a CANCELADO, restituir el stock de los productos (RN-03)
        if nuevo_estado == "CANCELADO" and pedido.estado != "CANCELADO":
            for detalle in pedido.items:
                producto = self.producto_repo.get_by_id(detalle.producto_id)
                if producto:
                    producto.stock += detalle.cantidad
                    self.session.add(producto)

        pedido.estado = nuevo_estado
        pedido.updated_at = datetime.now(UTC)
        return self.pedido_repo.update(pedido)

    def obtener_resumen(self) -> dict:
        return self.pedido_repo.get_resumen_estadisticas()

    def cancelar_pedido(self, pedido_id: int, usuario_id: int, es_admin: bool) -> Pedido:
        pedido = self.pedido_repo.get_by_id(pedido_id)
        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido no encontrado."
            )

        # Validar propiedad (si no es admin, debe ser su propio pedido) (RN-04)
        if not es_admin and pedido.usuario_id != usuario_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para cancelar un pedido ajeno."
            )

        # Validar que el pedido esté en estado PENDIENTE
        if pedido.estado != "PENDIENTE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se pueden cancelar pedidos que se encuentren en estado PENDIENTE."
            )

        # Restituir el stock de los productos (RN-03)
        for detalle in pedido.items:
            producto = self.producto_repo.get_by_id(detalle.producto_id)
            if producto:
                producto.stock += detalle.cantidad
                self.session.add(producto)

        pedido.estado = "CANCELADO"
        pedido.updated_at = datetime.now(UTC)
        return self.pedido_repo.update(pedido)