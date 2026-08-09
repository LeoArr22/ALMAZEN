from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from decimal import Decimal

# ==========================================
# 1. SCHEMAS PARA EL DETALLE (LOS RENGLONES)
# ==========================================

# Lo que nos manda el cliente para un producto del carrito
class VentaDetalleCreate(BaseModel):
    producto_id: int = Field(..., gt=0, examples=[1])
    cantidad: Decimal = Field(..., gt=0, examples=[0.500])

# Lo que la API devuelve para cada renglón individual de la venta
class VentaDetalleResponse(BaseModel):
    id: int
    producto_id: Optional[int]
    cantidad: Decimal
    precio_historico: Decimal
    costo_historico: Decimal

    model_config = {
        "from_attributes": True
    }


# ==========================================
# 2. SCHEMAS PARA LOS PAGOS (DESGLOSE)
# ==========================================

# Lo que nos manda el cliente para un desglose de pago
class VentaPagoCreate(BaseModel):
    medio_pago: str = Field(..., description="Efectivo, Transferencia, Tarjeta, etc.", examples=["Efectivo"])
    monto: Decimal = Field(..., ge=0, description="Monto abonado con este medio", examples=[1500.00])

# Lo que la API devuelve para un registro de pago
class VentaPagoResponse(BaseModel):
    id: int
    medio_pago: str
    monto: Decimal

    model_config = {
        "from_attributes": True
    }


# ==========================================
# 3. SCHEMAS PARA LA VENTA (LA CABECERA)
# ==========================================

# Request DTO: El cliente manda la lista de productos y la lista de medios de pago desde el POS
class VentaCreate(BaseModel):
    detalles: List[VentaDetalleCreate] = Field(..., min_length=1, description="Lista de productos en el carrito")
    pagos: List[VentaPagoCreate] = Field(..., min_length=1, description="Lista de pagos realizados")

# Response DTO: Lo que devolvemos al frontend (La venta completa armada)
class VentaResponse(BaseModel):
    id: int
    caja_id: int  
    fecha_venta: datetime
    total: Decimal
    ganancia_total: Decimal
    
    # RELACIÓN ANIDADA: La cabecera agrupa a todos sus renglones hijos
    detalles: List[VentaDetalleResponse] 

    # RELACIÓN ANIDADA: La cabecera agrupa todos los pagos realizados
    pagos: List[VentaPagoResponse]

    # Identificador único del usuario/empleado que procesó la transacción en el sistema
    usuario_id: int
    
    # Nombre de usuario legible extraído de la relación para renderizar en comprobantes o el historial
    username_vendedor: Optional[str] = None

    # Solo para auditoría: Si la venta fue anulada, este registro queda marcado como anulado (SoftDelete)
    es_anulada: bool = False

    model_config = {
        "from_attributes": True
    }