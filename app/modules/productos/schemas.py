from pydantic import BaseModel, Field, field_validator


class ProductoBase(BaseModel):
    """Esquema base que define los campos comunes para validación con Pydantic."""
    nombre: str = Field(..., min_length=1, json_schema_extra={"example": "Silla de Oficina"})
    descripcion: str = Field(..., min_length=3, json_schema_extra={"example": "Silla ergonómica de oficina"})
    precio_base: float = Field(ge=0, json_schema_extra={"example": 150.50})
    disponible: bool = True
    activo: bool = True
    imagen_url: list[str] = Field(default=[], json_schema_extra={"example": ["http://img.com/1.jpg"]})
    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("El nombre no puede estar vacío ni contener solo espacios")
        return value

class ProductoCreate(ProductoBase):
    """Esquema para la creación de un producto."""
    # Ya no incluimos categoria_ids acá, porque la vinculación 
    # se realiza posteriormente mediante el endpoint específico de relación.


class ProductoUpdate(BaseModel):
    """Esquema para actualización parcial o total de un producto."""
    nombre: str | None = Field(None, min_length=1)
    descripcion: str | None = Field(None, min_length=3)
    precio_base: float | None = Field(None, ge=0)
    disponible: bool | None = None
    activo: bool | None = None
    imagen_url: list[str] | None = None
    categoria_ids: list[int] | None = Field(default=None, description="IDs de categorías asociadas")
    ingrediente_ids: list[int] | None = Field(default=None, description="IDs de ingredientes asociados")

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value):
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("El nombre no puede estar vacío ni contener solo espacios")
        return value

class CategoriaResumen(BaseModel):
    """Esquema mínimo de categoría para anidar en la respuesta del producto."""
    id: int
    nombre: str
    descripcion: str

    class Config:
        from_attributes = True

class IngredienteResumen(BaseModel):
    """Esquema mínimo de ingrediente para anidar en la respuesta del producto."""
    id: int
    nombre: str
    descripcion: str
    alergenico: bool

    class Config:
        from_attributes = True  

class ProductoRead(ProductoBase):
    """Contrato de salida: incluye el ID generado y la lista de categorías asociadas."""
    id: int
    categorias: list[CategoriaResumen] = []
    ingredientes: list[IngredienteResumen] = []
    
    class Config:
        from_attributes = True
    
    
class ProductoStockResponse(BaseModel):
    """Esquema auxiliar para consulta de estado (mantenido del proyecto anterior)."""
    disponible: bool
    activo: bool
