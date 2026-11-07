from sqlmodel import Session, select

from app.core.repository import BaseRepository
from app.producto.models import Producto, Producto_Categoria, Producto_Ingrediente


class ProductoRepository(BaseRepository[Producto]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Producto)

    def get_by_nombre(self, nombre: str) -> Producto | None:
        producto = self.session.exec(
            select(Producto).where(Producto.nombre == nombre, Producto.activo == True)
        ).first()
        if producto:
            _ = producto.categorias
            _ = producto.ingredientes
            for cat in producto.categorias:
                self.session.expunge(cat)
            for ing in producto.ingredientes:
                self.session.expunge(ing)
            self.session.expunge(producto)
        return producto

    def get_all_paginated(self, skip: int = 0, limit: int = 20, activo: bool | None = None) -> list[Producto]:
        query = select(Producto)
        if activo is not None:
            query = query.where(Producto.activo == activo)
        
        productos = list(self.session.exec(query.offset(skip).limit(limit)).all())
        
        for prod in productos:
            # 1. Forzamos la carga de relaciones mientras la sesión está viva
            _ = prod.categorias
            _ = prod.ingredientes
            
            # 2. Desvinculamos individualmente cada categoría hija
            for cat in prod.categorias:
                self.session.expunge(cat)
                
            # 3. Desvinculamos individualmente cada ingrediente hijo
            for ing in prod.ingredientes:
                self.session.expunge(ing)
                
            # 4. Desvinculamos el producto principal de la sesión
            self.session.expunge(prod)
            
        return productos

    def get_duplicado_update(self, id: int, nombre: str) -> Producto | None:
        producto = self.session.exec(
            select(Producto).where(
                (Producto.id != id) & 
                (Producto.activo == True) & 
                (Producto.nombre == nombre)
            )
        ).first()
        if producto:
            self.session.expunge(producto)
        return producto

    def get_producto_activo_por_categoria(self, categoria_id: int) -> Producto | None:
        statement = (
            select(Producto)
            .join(Producto_Categoria)
            .where(Producto_Categoria.categoria_id == categoria_id, Producto.activo == True)
        )
        producto = self.session.exec(statement).first()
        if producto:
            _ = producto.categorias
            _ = producto.ingredientes
            for cat in producto.categorias:
                self.session.expunge(cat)
            for ing in producto.ingredientes:
                self.session.expunge(ing)
            self.session.expunge(producto)
        return producto

    def get_relacion(self, producto_id: int, categoria_id: int) -> Producto_Categoria | None:
        relacion = self.session.exec(
            select(Producto_Categoria).where(
                Producto_Categoria.producto_id == producto_id,
                Producto_Categoria.categoria_id == categoria_id
            )
        ).first()
        if relacion:
            self.session.expunge(relacion)
        return relacion

    def get_all_relaciones(self) -> list[Producto_Categoria]:
        relaciones = list(self.session.exec(select(Producto_Categoria)).all())
        for rel in relaciones:
            self.session.expunge(rel)
        return relaciones

    # MÉTODOS PARA INGREDIENTES
    def get_relacion_ingrediente(self, producto_id: int, ingrediente_id: int) -> Producto_Ingrediente | None:
        relacion = self.session.exec(
            select(Producto_Ingrediente).where(
                Producto_Ingrediente.producto_id == producto_id,
                Producto_Ingrediente.ingrediente_id == ingrediente_id
            )
        ).first()
        if relacion:
            self.session.expunge(relacion)
        return relacion

    def get_all_relaciones_ingredientes(self) -> list[Producto_Ingrediente]:
        relaciones = list(self.session.exec(select(Producto_Ingrediente)).all())
        for rel in relaciones:
            self.session.expunge(rel)
        return relaciones

    def get_producto_activo_por_ingrediente(self, ingrediente_id: int) -> Producto | None:
        statement = (
            select(Producto)
            .join(Producto_Ingrediente)
            .where(Producto_Ingrediente.ingrediente_id == ingrediente_id, Producto.activo == True)
        )
        producto = self.session.exec(statement).first()
        if producto:
            _ = producto.categorias
            _ = producto.ingredientes
            for cat in producto.categorias:
                self.session.expunge(cat)
            for ing in producto.ingredientes:
                self.session.expunge(ing)
            self.session.expunge(producto)
        return producto

    def tiene_pedidos_activos(self, producto_id: int) -> bool:
        from app.pedido.models import DetallePedido, Pedido
        statement = (
            select(Pedido)
            .join(DetallePedido)
            .where(DetallePedido.producto_id == producto_id, Pedido.activo == True)
        )
        pedido_activo = self.session.exec(statement).first()
        return pedido_activo is not None

    