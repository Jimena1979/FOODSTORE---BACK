from typing import TYPE_CHECKING

from sqlmodel import (
    ARRAY,
    Column,
    Field,
    ForeignKey,
    Integer,
    Relationship,
    SQLModel,
    String,
)

if TYPE_CHECKING:
    from app.categoria.models import Categoria
    from app.ingrediente.models import Ingrediente
    from app.pedido.models import DetallePedido


# 1. Tabla de enlace con el nombre exacto del TP
class Producto_Categoria(SQLModel, table=True):
    __tablename__ = "producto_categoria"

    producto_id: int = Field(
        sa_column=Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    )
    categoria_id: int = Field(
        sa_column=Column(Integer, ForeignKey("categorias.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    )

# NUEVO: Tabla de enlace N:N entre Producto e Ingrediente
class Producto_Ingrediente(SQLModel, table=True):
    __tablename__ = "producto_ingrediente"

    producto_id: int = Field(
        sa_column=Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    )
    ingrediente_id: int = Field(
        sa_column=Column(Integer, ForeignKey("ingredientes.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    )


# 2. Schema base con validaciones (precio >= 0) y los campos del nuevo TP
class ProductoBase(SQLModel):
    nombre: str = Field(index=True, min_length=1)
    descripcion: str
    precio_base: float = Field(ge=0)  # Mantenemos la validación de que no sea negativo
    disponible: bool = Field(default=True)
    activo: bool = Field(default=True)  # Baja lógica incluida en la base
    imagen_url: list[str] = Field(default=[], sa_column=Column(ARRAY(String)))

 
# 3. Clase Producto que hereda de ProductoBase, agrega id, y la relación
class Producto(ProductoBase, table=True):
    __tablename__ = "productos"

    id: int | None = Field(default=None, primary_key=True)
   

    # Relación N:N con Categorías
    categorias: list["Categoria"] = Relationship(
        back_populates="productos",
        #nos conectamos con la tabla puente
        link_model=Producto_Categoria
    )
    # NUEVO: Relación N:N con Ingredientes
    ingredientes: list["Ingrediente"] = Relationship(
        back_populates="productos",
        link_model=Producto_Ingrediente
    )

    detalles_pedido: list["DetallePedido"] = Relationship(back_populates="producto")