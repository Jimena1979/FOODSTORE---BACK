from fastapi import HTTPException, status

from app.producto.models import Producto, Producto_Categoria, Producto_Ingrediente
from app.producto.schemas import ProductoCreate, ProductoStockResponse, ProductoUpdate
from app.producto.unit_of_work import ProductoUnitOfWork


def crear(data: ProductoCreate) -> Producto:
    with ProductoUnitOfWork() as uow:
        existe = uow.productos.get_by_nombre(data.nombre)
        if existe:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un producto activo con el nombre '{data.nombre}'",
            )

        nuevo_producto = Producto(**data.model_dump())
        uow._session.add(nuevo_producto)
        uow._session.flush()
        uow._session.refresh(nuevo_producto)
        
        # Forzar carga y desvincular relaciones hijas
        _ = nuevo_producto.categorias
        _ = nuevo_producto.ingredientes
        for cat in nuevo_producto.categorias:
            uow._session.expunge(cat)
        for ing in nuevo_producto.ingredientes:
            uow._session.expunge(ing)
        uow._session.expunge(nuevo_producto)
        
        return nuevo_producto

def obtener_todos(skip: int = 0, limit: int = 20, activo: bool | None = None) -> list[Producto]:
    with ProductoUnitOfWork() as uow:
        return uow.productos.get_all_paginated(skip, limit, activo)


def obtener_por_id(id: int) -> Producto:
    with ProductoUnitOfWork() as uow:
        producto = uow.productos.get_by_id(id)
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        _ = producto.categorias
        _ = producto.ingredientes
        uow._session.expunge(producto)
        return producto


def actualizar_total(id: int, data: ProductoUpdate) -> Producto:
    with ProductoUnitOfWork() as uow:
        producto = uow.productos.get_by_id(id)
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        if data.nombre and data.nombre != producto.nombre:
            existe = uow.productos.get_duplicado_update(id, data.nombre)
            if existe:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ya existe otro producto activo con el nombre '{data.nombre}'",
                )

        cambios = data.model_dump(exclude_unset=True)
        producto.sqlmodel_update(cambios)

        uow._session.add(producto)
        uow._session.flush()
        uow._session.refresh(producto)
        
        # Forzar carga y desvincular relaciones hijas para evitar DetachedInstanceError en el PUT
        _ = producto.categorias
        _ = producto.ingredientes
        for cat in producto.categorias:
            uow._session.expunge(cat)
        for ing in producto.ingredientes:
            uow._session.expunge(ing)
        uow._session.expunge(producto)
        
        return producto


def vincular_categoria(producto_id: int, categoria_id: int):
    with ProductoUnitOfWork() as uow:
        producto = uow.productos.get_by_id(producto_id)
        categoria = uow.categorias.get_by_id(categoria_id)

        if not producto or not producto.activo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Producto no encontrado o se encuentra inactivo (dado de baja)"
            )
            
        if not categoria or not categoria.activo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Categoría no encontrada o se encuentra inactiva (dada de baja)"
            )
        
        existente = uow.productos.get_relacion(producto_id, categoria_id)
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El producto ya tiene asignada esa categoría"
            )

        nuevo_link = Producto_Categoria(producto_id=producto_id, categoria_id=categoria_id)
        uow._session.add(nuevo_link)
        uow._session.flush()
        
        return {"message": f"Producto '{producto.nombre}' asignado a la categoría '{categoria.nombre}'"}


# ==========================================
# MÉTODOS PARA INGREDIENTES
# ==========================================

def vincular_ingrediente(producto_id: int, ingrediente_id: int):
    with ProductoUnitOfWork() as uow:
        producto = uow.productos.get_by_id(producto_id)
        ingrediente = uow.ingredientes.get_by_id(ingrediente_id)

        if not producto or not producto.activo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Producto no encontrado o se encuentra inactivo (dado de baja)"
            )
            
        if not ingrediente or not ingrediente.activo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Ingrediente no encontrado o se encuentra inactivo (dado de baja)"
            )
        
        existente = uow.productos.get_relacion_ingrediente(producto_id, ingrediente_id)
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El producto ya tiene asignado ese ingrediente"
            )

        nuevo_link = Producto_Ingrediente(producto_id=producto_id, ingrediente_id=ingrediente_id)
        uow._session.add(nuevo_link)
        uow._session.flush()
        
        return {"message": f"Ingrediente '{ingrediente.nombre}' añadido al producto '{producto.nombre}'"}


def desvincular_ingrediente(producto_id: int, ingrediente_id: int):
    with ProductoUnitOfWork() as uow:
        relacion = uow.productos.get_relacion_ingrediente(producto_id, ingrediente_id)
        if not relacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La relación entre el producto y el ingrediente no existe."
            )
            
        uow._session.delete(relacion)
        uow._session.flush()
        
        return {"message": "Ingrediente desvinculado del producto exitosamente"}


def listar_relaciones_ingredientes():
    with ProductoUnitOfWork() as uow:
        return uow.productos.get_all_relaciones_ingredientes()


# ==========================================

def desactivar(id: int) -> Producto:
    with ProductoUnitOfWork() as uow:
        producto = uow.productos.get_by_id(id)
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        if not producto.activo:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El producto ya está inactivo"
            )

        # REGLA DE NEGOCIO: Bloquear baja si el producto está en un pedido activo
        if uow.productos.tiene_pedidos_activos(id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede dar de baja el producto porque está asociado a un pedido activo."
            )

        producto.activo = False
        uow._session.add(producto)
        uow._session.flush()
        uow._session.refresh(producto)
        
        # Forzar carga y desvincular relaciones para evitar errores de serialización
        _ = producto.categorias
        _ = producto.ingredientes
        for cat in producto.categorias:
            uow._session.expunge(cat)
        for ing in producto.ingredientes:
            uow._session.expunge(ing)
        uow._session.expunge(producto)
        
        return producto

def obtener_estado_stock(id: int) -> ProductoStockResponse:
    with ProductoUnitOfWork() as uow:
        producto = uow.productos.get_by_id(id)
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        return ProductoStockResponse(
            disponible=producto.disponible,
            activo=producto.activo,
        )


def desvincular_categoria(producto_id: int, categoria_id: int):
    with ProductoUnitOfWork() as uow:
        relacion = uow.productos.get_relacion(producto_id, categoria_id)
        if not relacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La relación especificada no existe."
            )
            
        uow._session.delete(relacion)
        uow._session.flush()
        
        return {"message": "Producto desvinculado de la categoría exitosamente"}


def listar_relaciones():
    with ProductoUnitOfWork() as uow:
        return uow.productos.get_all_relaciones()