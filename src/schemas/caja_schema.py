from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from decimal import Decimal

# ==========================================
# 1. SCHEMAS DE ENTRADA (REQUEST DTOs)
# ==========================================

# Esquema Base: Campos comunes
class CajaBase(BaseModel):
    monto_inicial: Decimal = Field(default=0.00, ge=0, examples=[5000.00])

# Request DTO: Para ABRIR la caja (Solo requiere el monto inicial)
class CajaCreate(CajaBase):
    pass

# Request DTO: Para CERRAR la caja (Solo requiere el monto final real)
class CajaClose(BaseModel):
    monto_final_real: Decimal = Field(ge=0, examples=[28500.00])


# ==========================================
# 2. SCHEMAS DE SALIDA (RESPONSE DTOs)
# ==========================================

# Lo que la API devuelve (Conserva tus campos y agrega auditoría al final)
class CajaResponse(CajaBase):
    id: int
    fecha_apertura: datetime
    fecha_cierre: Optional[datetime] = None
    monto_final_estimado: Decimal = Field(default=Decimal("0.00"))
    monto_final_real: Optional[Decimal] = None
    estado: str

    # Identificador único del usuario que realizó la apertura del turno
    usuario_apertura_id: int
    
    # Nombre legible del usuario que abrió la caja (para auditoría visual)
    username_apertura: Optional[str] = None

    # Identificador único del usuario que realizó el cierre (nullable hasta que se cierre)
    usuario_cierre_id: Optional[int] = None
    
    # Nombre legible del usuario que cerró la caja
    username_cierre: Optional[str] = None

    model_config = {
        "from_attributes": True
    }