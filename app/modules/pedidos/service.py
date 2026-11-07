from fastapi import HTTPException, status

from app.pedido.models import DetallePedido, Pedido
from app.pedido.schemas import DetallePedidoCreate, PedidoCreate, PedidoUpdateEstado
from app.pedido.unit_of_work import PedidoUnitOfWork

# Lista de estados válidos permitidos para los pedidos
ESTADOS_PERMITIDOS = {"PENDIENTE", "EN_PROCESO", "COMPLETADO", "CANCELADO"}


def crear_pedido(data: PedidoCreate) -> Pedido:
    with PedidoUnitOfWork() as uow:
        if not data.detalles:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Un pedido debe tener al menos un DetallePedido para ser creado (RN-12)."
            )

        # PUNTO 3: Validar productos duplicados en los detalles para evitar error 500
        productos_ids = [item.producto_id for item in data.detalles]
        if len(productos_ids) != len(set(productos_ids)):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se puede repetir el mismo producto en los detalles del pedido."
            )

        subtotal_calculado = 0.0
        detalles_a_crear = []

        for item in data.detalles:
            producto = uow.productos.get_by_id(item.producto_id)
            if not producto or not producto.activo:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Producto con ID {item.producto_id} no encontrado o inactivo."
                )

            if not producto.disponible:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El producto '{producto.nombre}' no se encuentra disponible actualmente para la venta."
                )

            # PUNTO 2: Tomar el precio real del producto (snapshot) y NO el que manda el cliente
            precio_unitario_real = producto.precio_base
            item_subtotal = item.cantidad * precio_unitario_real
            subtotal_calculado += item_subtotal

            detalle = DetallePedido(
                producto_id=item.producto_id,
                cantidad=item.cantidad,
                nombre_producto_snap=producto.nombre,
                precio_unitario_snap=precio_unitario_real, # <--- Usamos el precio real de la BD
                subtotal_snap=item_subtotal,
                personalizacion=item.personalizacion
            )
            detalles_a_crear.append(detalle)

        total_final = max(0.0, subtotal_calculado - data.descuento + data.costo_envio)

        # Validar estado inicial si viene customizado
        estado_a_guardar = data.estado_codigo.upper()
        if estado_a_guardar not in ESTADOS_PERMITIDOS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Estado de pedido inválido. Estados permitidos: {list(ESTADOS_PERMITIDOS)}"
            )

        nuevo_pedido = Pedido(
            usuario_id=data.usuario_id,
            direccion_id=data.direccion_id,
            estado_codigo=estado_a_guardar,
            forma_pago_codigo=data.forma_pago_codigo,
            subtotal=subtotal_calculado,
            descuento=data.descuento,
            costo_envio=data.costo_envio,
            total=total_final,
            notas=data.notas,
            detalles=detalles_a_crear
        )

        uow._session.add(nuevo_pedido)
        uow._session.flush()
        uow._session.refresh(nuevo_pedido)
        
        _ = nuevo_pedido.detalles
        uow._session.expunge(nuevo_pedido)
        return nuevo_pedido


def listar_pedidos(skip: int = 0, limit: int = 20, activo: bool | None = True) -> list[Pedido]:
    with PedidoUnitOfWork() as uow:
        pedidos = uow.pedidos.get_all_paginated(skip, limit, activo)
        for p in pedidos:
            _ = p.detalles
            uow._session.expunge(p)
        return pedidos


def obtener_por_id(id: int) -> Pedido:
    with PedidoUnitOfWork() as uow:
        pedido = uow.pedidos.get_by_id_activo(id)
        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido no encontrado (RN-13)"
            )
        _ = pedido.detalles
        uow._session.expunge(pedido)
        return pedido


def actualizar_estado(id: int, data: PedidoUpdateEstado) -> Pedido:
    with PedidoUnitOfWork() as uow:
        pedido = uow.pedidos.get_by_id_activo(id)
        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido no encontrado (RN-13)"
            )

        # PUNTO 3: Validar que el estado pertenezca a la lista permitida
        nuevo_estado = data.estado_codigo.upper()
        if nuevo_estado not in ESTADOS_PERMITIDOS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Estado '{data.estado_codigo}' inválido. Los estados permitidos son: {list(ESTADOS_PERMITIDOS)}"
            )

        pedido.estado_codigo = nuevo_estado
        uow._session.add(pedido)
        uow._session.flush()
        uow._session.refresh(pedido)
        _ = pedido.detalles
        uow._session.expunge(pedido)
        return pedido


def agregar_detalle_a_pedido(pedido_id: int, item: DetallePedidoCreate) -> Pedido:
    with PedidoUnitOfWork() as uow:
        pedido = uow.pedidos.get_by_id_activo(pedido_id)
        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido no encontrado (RN-13)"
            )

        # Verificar si el producto ya existe en los detalles actuales de este pedido
        if any(d.producto_id == item.producto_id for d in pedido.detalles):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El producto ya se encuentra en este pedido. Actualice la cantidad en su lugar."
            )

        producto = uow.productos.get_by_id(item.producto_id)
        if not producto or not producto.activo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {item.producto_id} no encontrado o inactivo."
            )

        if not producto.disponible:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El producto '{producto.nombre}' no se encuentra disponible actualmente."
            )

        # Snapshot del precio real
        precio_unitario_real = producto.precio_base
        item_subtotal = item.cantidad * precio_unitario_real

        nuevo_detalle = DetallePedido(
            pedido_id=pedido_id,
            producto_id=item.producto_id,
            cantidad=item.cantidad,
            nombre_producto_snap=producto.nombre,
            precio_unitario_snap=precio_unitario_real,
            subtotal_snap=item_subtotal,
            personalizacion=item.personalizacion
        )

        pedido.detalles.append(nuevo_detalle)
        pedido.subtotal += item_subtotal
        pedido.total = max(0.0, pedido.subtotal - pedido.descuento + pedido.costo_envio)

        uow._session.add(pedido)
        uow._session.flush()
        uow._session.refresh(pedido)
        _ = pedido.detalles
        uow._session.expunge(pedido)
        return pedido


def desactivar_pedido(id: int) -> Pedido:
    with PedidoUnitOfWork() as uow:
        pedido = uow.pedidos.get_by_id_activo(id)
        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido no encontrado (RN-13)"
            )

        pedido.activo = False
        uow._session.add(pedido)
        uow._session.flush()
        uow._session.refresh(pedido)
        _ = pedido.detalles
        uow._session.expunge(pedido)
        return pedido