# src/services/libro_service.py
import calendar
from datetime import datetime, date, timedelta, time
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.repositories.libro_repository import LibroRepository
from src.schemas.libro_schema import LibroDiarioResponse, DesglosePagoResponse 

class LibroService:

    @staticmethod
    def obtener_libro_diario(
        db: Session, 
        periodo: str = "dia", 
        fecha_ref: Optional[date] = None,
        fecha_inicio_custom: Optional[date] = None,
        fecha_fin_custom: Optional[date] = None
    ) -> LibroDiarioResponse:
        
        base_date = fecha_ref or date.today()
        periodo_lower = periodo.lower()

        # 1. Determinar el rango de fechas según la estrategia elegida
        if periodo_lower == "dia":
            dt_inicio = datetime.combine(base_date, time.min)
            dt_fin = datetime.combine(base_date, time.max)
            
        elif periodo_lower == "semana":
            inicio_semana = base_date - timedelta(days=base_date.weekday())
            fin_semana = inicio_semana + timedelta(days=6)
            dt_inicio = datetime.combine(inicio_semana, time.min)
            dt_fin = datetime.combine(fin_semana, time.max)
            
        elif periodo_lower == "mes":
            inicio_mes = base_date.replace(day=1)
            _, ultimo_dia = calendar.monthrange(base_date.year, base_date.month)
            fin_mes = base_date.replace(day=ultimo_dia)
            dt_inicio = datetime.combine(inicio_mes, time.min)
            dt_fin = datetime.combine(fin_mes, time.max)
                    
        elif periodo_lower == "personalizado":
            if not fecha_inicio_custom or not fecha_fin_custom:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Para el período 'personalizado' debe indicar fecha_inicio_custom y fecha_fin_custom."
                )
            if fecha_inicio_custom > fecha_fin_custom:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La fecha de inicio no puede ser posterior a la fecha de fin."
                )
            dt_inicio = datetime.combine(fecha_inicio_custom, time.min)
            dt_fin = datetime.combine(fecha_fin_custom, time.max)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Período no válido. Opciones permitidas: 'dia', 'semana', 'mes', 'personalizado'."
            )

        # 2. Consultar repositorio
        totales = LibroRepository.obtener_totales_periodo(db, dt_inicio, dt_fin)
        pagos_raw = LibroRepository.obtener_desglose_pagos(db, dt_inicio, dt_fin)
        anulaciones = LibroRepository.obtener_auditoria_anulaciones(db, dt_inicio, dt_fin)

        # 3. Mapear explícitamente los diccionarios a objetos Pydantic para el linter
        desglose_pagos_schema = [
            DesglosePagoResponse(
                medio_pago=str(p["medio_pago"]), 
                monto_total=p["monto_total"]
            ) 
            for p in pagos_raw
        ]

        # 4. Retornar DTO consolidado
        return LibroDiarioResponse(
            periodo_consultado=periodo_lower,
            fecha_inicio=dt_inicio.date(),
            fecha_fin=dt_fin.date(),
            total_facturado=totales["total_facturado"],
            costo_total_mercaderia=totales["costo_total_mercaderia"],
            ganancia_neta_total=totales["ganancia_neta_total"],
            cantidad_transacciones=totales["cantidad_transacciones"],
            ticket_promedio=totales["ticket_promedio"],
            cantidad_ventas_anuladas=anulaciones["cantidad_ventas_anuladas"],
            monto_total_anulado=anulaciones["monto_total_anulado"],
            desglose_pagos=desglose_pagos_schema # Pasar la lista de schemas tipados
        )