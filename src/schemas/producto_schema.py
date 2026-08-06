from pydantic import BaseModel, Field, field_validator
from typing import Optional
from decimal import Decimal
import re

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

    # 🌟 VALIDACIÓN INTELIGENTE
    @field_validator('codigo_barras')
    @classmethod
    def validar_codigo_barras(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "":
            return None  # Si viene vacío, lo limpiamos y dejamos en None
        
        # Le quitamos espacios locos por las dudas
        codigo = v.strip()
        
        # Validamos que sean SOLO números y que tengan un largo estándar de comercio (entre 8 y 14 dígitos)
        if not re.match(r"^\d{8,14}$", codigo):
            raise ValueError(
                "El código de barras debe contener entre 8 y 14 dígitos numéricos solamente."
            )
            
        return codigo

# 2. Request DTO: Para CREAR un producto (Se usa tal cual la Base)
class ProductoCreate(ProductoBase):
    pass

# 3. Request DTO: Para EDITAR un producto (Todos los campos pasan a ser opcionales)
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

# 4. Response DTO: Lo que la API le va a devolver al cliente (Agrega el ID)
class ProductoResponse(ProductoBase):
    id: int

    # Esta subclase es OBLIGATORIA en Pydantic v2 para que pueda leer 
    # los modelos de SQLAlchemy directos del repositorio y transformarlos a JSON
    model_config = {
        "from_attributes": True
    }