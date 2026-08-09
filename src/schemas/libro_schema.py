# src/schemas/libro_schema.py
from pydantic import BaseModel, Field
from datetime import date
from decimal import Decimal
from typing import List, Dict

class DesglosePagoResponse(BaseModel):
    medio_pago: str
    monto_total: Decimal

class LibroDiarioResponse(BaseModel):
    periodo_consultado: str = Field(..., examples=["dia", "semana", "mes", "personalizado"])
    fecha_inicio: date
    fecha_fin: date
    
    # Métricas consolidadas
    total_facturado: Decimal
    costo_total_mercaderia: Decimal
    ganancia_neta_total: Decimal
    cantidad_transacciones: int
    ticket_promedio: Decimal
    
    # Auditoría de anulaciones
    cantidad_ventas_anuladas: int
    monto_total_anulado: Decimal

    # Desglose por Medio de Pago (Efectivo, Mercado Pago, Tarjetas, etc.)
    desglose_pagos: List[DesglosePagoResponse]

    model_config = {
        "from_attributes": True
    }