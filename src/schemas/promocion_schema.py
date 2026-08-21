from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal

class PromocionProductoItem(BaseModel):
    producto_id: int = Field(..., gt=0)
    cantidad_requerida: Decimal = Field(..., gt=0, examples=[3.000])

class PromocionBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, examples=["2x1 Fernet + Coca", "3x2 Cerveza", "Mayorista +5u"])
    descripcion: Optional[str] = Field(None, max_length=255)
    # 🌟 Tipos soportados: MULTIPLO (lotes x $X), CANTIDAD_MINIMA (mayorista) y COMBO (varios productos)
    tipo: str = Field(default="MULTIPLO", examples=["MULTIPLO", "CANTIDAD_MINIMA", "COMBO", "CANTIDAD"])
    precio_promocional: Decimal = Field(..., gt=0, examples=[5000.00])
    activo: bool = Field(default=True)

class PromocionCreate(PromocionBase):
    productos: List[PromocionProductoItem] = Field(..., min_length=1) 
    
class PromocionUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    tipo: Optional[str] = Field(None)
    precio_promocional: Optional[Decimal] = Field(None, gt=0)
    activo: Optional[bool] = Field(None)
    productos: Optional[List[PromocionProductoItem]] = Field(None)

class PromocionProductoResponse(BaseModel):
    id: int
    producto_id: int
    cantidad_requerida: Decimal

    model_config = {"from_attributes": True}

class PromocionResponse(PromocionBase):
    id: int
    productos: List[PromocionProductoResponse]

    model_config = {"from_attributes": True}