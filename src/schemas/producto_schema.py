from pydantic import BaseModel, Field, field_validator
from typing import Optional
from decimal import Decimal
import re
import unicodedata

# 1. Esquema Base: Campos comunes que comparten todos los DTOs de Producto
class ProductoBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, examples=["Fideos Marolio 500g"])
    descripcion: Optional[str] = Field(None, max_length=255, examples=["Fideos tallarín"])
    categoria: str = Field(..., min_length=2, max_length=50, examples=["Almacén"])
    stock: Decimal = Field(default=Decimal("0.000"), ge=0)  
    costo: Decimal = Field(..., gt=0, examples=[450.00])
    precio: Decimal = Field(..., gt=0, examples=[750.00])
    codigo_barras: Optional[str] = Field(default=None)
    es_fraccionable: bool = Field(default=False)
    unidad_medida: str = Field(default="UNIDAD")

    # 🌟 NORMALIZACIÓN DE CATEGORÍA (Capitalize + Sin tildes)
    @field_validator('categoria')
    @classmethod
    def normalizar_categoria(cls, v: Optional[str]) -> Optional[str]:
        if not v or not v.strip():
            return v
        # Remover tildes
        sin_tildes = ''.join(
            c for c in unicodedata.normalize('NFD', v) 
            if unicodedata.category(c) != 'Mn'
        )
        # Formato Capitalize sin tildes (ej: "almacén y golosínas" -> "Almacen y golosinas")
        limpia = sin_tildes.strip()
        return limpia.capitalize() if limpia else limpia

    # 🌟 VALIDACIÓN INTELIGENTE DE CÓDIGO DE BARRAS
    @field_validator('codigo_barras')
    @classmethod
    def validar_codigo_barras(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "":
            return None
        
        codigo = v.strip()
        if not re.match(r"^\d{8,14}$", codigo):
            raise ValueError(
                "El código de barras debe contener entre 8 y 14 dígitos numéricos solamente."
            )
            
        return codigo

# 2. Request DTO: Para CREAR un producto
class ProductoCreate(ProductoBase):
    pass

# 3. Request DTO: Para EDITAR un producto
class ProductoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    codigo_barras: Optional[str] = Field(None, min_length=8, max_length=14)
    descripcion: Optional[str] = Field(None, max_length=255)
    categoria: Optional[str] = Field(None, min_length=2, max_length=50)
    stock: Decimal = Field(default=Decimal("0.000"), ge=0)  
    es_fraccionable: Optional[bool] = Field(None)
    unidad_medida: Optional[str] = Field(None, min_length=2, max_length=20)
    costo: Optional[Decimal] = Field(None, gt=0)
    precio: Optional[Decimal] = Field(None, gt=0)

    # Reutilizamos el sanitizador de categoría para actualizaciones opcionales
    @field_validator('categoria')
    @classmethod
    def normalizar_categoria_update(cls, v: Optional[str]) -> Optional[str]:
        return ProductoBase.normalizar_categoria(v)

    @field_validator('codigo_barras')
    @classmethod
    def validar_codigo_barras_update(cls, v: Optional[str]) -> Optional[str]:
        return ProductoBase.validar_codigo_barras(v)

# 4. Response DTO: Lo que la API le va a devolver al cliente
class ProductoResponse(ProductoBase):
    id: int

    model_config = {
        "from_attributes": True
    }