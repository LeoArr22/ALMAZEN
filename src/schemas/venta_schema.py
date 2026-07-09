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
    cantidad: int = Field(..., gt=0, examples=[3])

# Lo que la API devuelve para cada renglón individual de la venta
class VentaDetalleResponse(BaseModel):
    id: int
    producto_id: int
    cantidad: int
    precio_historico: Decimal
    costo_historico: Decimal

    model_config = {
        "from_attributes": True
    }


# ==========================================
# 2. SCHEMAS PARA LA VENTA (LA CABECERA)
# ==========================================

# Request DTO: El cliente solo manda la lista de productos y cantidades desde el POS
class VentaCreate(BaseModel):
    detalles: List[VentaDetalleCreate] = Field(..., min_length=1, description="Lista de productos en el carrito")

# Response DTO: Lo que devolvemos al frontend (La venta completa armada)
class VentaResponse(BaseModel):
    id: int
    caja_id: int  
    fecha_venta: datetime
    total: Decimal
    ganancia_total: Decimal
    
    # RELACIÓN ANIDADA: La cabecera agrupa a todos sus renglones hijos
    detalles: List[VentaDetalleResponse] 

    # Identificador único del usuario/empleado que procesó la transacción en el sistema
    usuario_id: int
    
    # Nombre de usuario legible extraído de la relación para renderizar en comprobantes o el historial
    username_vendedor: Optional[str] = None

    model_config = {
        "from_attributes": True
    }