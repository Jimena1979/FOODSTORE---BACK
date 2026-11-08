from fastapi import HTTPException, status

from app.modules.productos.models import Producto
from app.modules.productos.schemas import (
    ProductoCreate,
    ProductoRead,
    ProductosPaginados,
    ProductoStockUpdate,
    ProductoUpdate,
)


class ProductoService:
    def __init__(self, uow):
        self.uow = uow

    def listar_productos(
        self,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
        categoria_id: int | None = None,
        disponible: bool | None = None,
    ) -> ProductosPaginados:
        with self.uow as uow:
            items, total = uow.productos.search(
                skip=skip,
                limit=limit,
                search=search,
                categoria_id=categoria_id,
                disponible=disponible,
                solo_activos=True
            )
            return ProductosPaginados(
                total=total,
                items=[ProductoRead.model_validate(p) for p in items]
            )

    def obtener_por_id(self, producto_id: int) -> ProductoRead:
        with self.uow as uow:
            producto = uow.productos.get_by_id(producto_id)
            if not producto or not producto.activo:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Producto no encontrado",
                )
            return ProductoRead.model_validate(producto)

    def crear_producto(self, data: ProductoCreate) -> ProductoRead:
        with self.uow as uow:
            # 1. Validar que la categoría exista y esté activa (Requisito TPI)[cite: 13]
            categoria = uow.categorias.get_by_id(data.categoria_id)
            if not categoria or not categoria.activo:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Categoría no encontrada o inactiva",
                )
            
            # 2. Validar tu regla de negocio: que no exista otro producto ACTIVO con el mismo nombre
            productos_existentes, _ = uow.productos.search(search=data.nombre, solo_activos=True)
            for p in productos_existentes:
                if p.nombre.strip().lower() == data.nombre.strip().lower():
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Ya existe un producto activo con ese nombre",
                    )
            
            producto = Producto(**data.model_dump())
            uow.productos.add(producto)
            return ProductoRead.model_validate(producto)

    def actualizar_producto(self, producto_id: int, data: ProductoUpdate) -> ProductoRead:
        with self.uow as uow:
            producto = uow.productos.get_by_id(producto_id)
            if not producto or not producto.activo:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Producto no encontrado",
                )
            
            update_data = data.model_dump(exclude_unset=True)

            # Si se actualiza el nombre, verificar colisión con otro producto activo
            if update_data.get("nombre"):
                nuevo_nombre = update_data["nombre"]
                productos_existentes, _ = uow.productos.search(search=nuevo_nombre, solo_activos=True)
                for p in productos_existentes:
                    if p.id != producto_id and p.nombre.strip().lower() == nuevo_nombre.strip().lower():
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="Ya existe otro producto activo con ese nombre",
                        )

            # Si se actualiza la categoría, validar que exista y esté activa[cite: 13]
            if "categoria_id" in update_data:
                categoria = uow.categorias.get_by_id(update_data["categoria_id"])
                if not categoria or not categoria.activo:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="La nueva categoría no existe o está dada de baja",
                    )

            for key, value in update_data.items():
                setattr(producto, key, value)
            
            uow.productos.add(producto)
            return ProductoRead.model_validate(producto)

    def actualizar_stock(self, producto_id: int, data: ProductoStockUpdate) -> ProductoRead:
        with self.uow as uow:
            producto = uow.productos.get_by_id(producto_id)
            if not producto or not producto.activo:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Producto no encontrado",
                )
            
            producto.stock = data.stock
            producto.disponible = data.disponible
            uow.productos.add(producto)
            return ProductoRead.model_validate(producto)

    def baja_logica(self, producto_id: int) -> None:
        with self.uow as uow:
            producto = uow.productos.get_by_id(producto_id)
            if not producto or not producto.activo:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Producto no encontrado",
                )
            producto.activo = False
            uow.productos.add(producto)