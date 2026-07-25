# src/schemas/caja_schema.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from decimal import Decimal

# ==========================================
# 0. SCHEMAS AUXILIARES
# ==========================================
class UsuarioEnCaja(BaseModel):
    id: int
    username: str
    nombre: Optional[str] = None
    
    model_config = {
        "from_attributes": True
    }

# ==========================================
# 1. SCHEMAS DE ENTRADA (REQUEST DTOs)
# ==========================================
class CajaBase(BaseModel):
    monto_inicial: Decimal = Field(default=0.00, ge=0, examples=[5000.00])

class CajaCreate(CajaBase):
    pass

class CajaClose(BaseModel):
    monto_final_real: Decimal = Field(ge=0, examples=[28500.00])

# ==========================================
# 2. SCHEMAS DE SALIDA (RESPONSE DTOs)
# ==========================================
class CajaResponse(BaseModel):
    id: int
    fecha_apertura: datetime
    fecha_cierre: Optional[datetime] = None  
    monto_inicial: Decimal
    monto_final_estimado: Optional[Decimal] = None  
    monto_final_real: Optional[Decimal] = None  
    estado: str
    usuario_apertura_id: int
    usuario_cierre_id: Optional[int] = None 
    
    # 👥 Relaciones cargadas desde SQLAlchemy para auditoría completa
    usuario_apertura: Optional[UsuarioEnCaja] = None
    usuario_cierre: Optional[UsuarioEnCaja] = None

    model_config = {
        "from_attributes": True
    }