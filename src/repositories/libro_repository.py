from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from src.models.venta import Venta
from src.models.venta_pago import VentaPago

class LibroRepository:

    @staticmethod
    def obtener_totales_periodo(db: Session, fecha_inicio: datetime, fecha_fin: datetime) -> dict:
        stmt = select(
            func.coalesce(func.sum(Venta.total), Decimal("0.00")).label("total_facturado"),
            func.coalesce(func.sum(Venta.ganancia_total), Decimal("0.00")).label("ganancia_neta_total"),
            func.count(Venta.id).label("cantidad_transacciones")
        ).where(
            and_(
                Venta.fecha_venta >= fecha_inicio,
                Venta.fecha_venta <= fecha_fin,
                Venta.es_anulada == False
            )
        )

        resultado = db.execute(stmt).first()

        if not resultado:
            return {
                "total_facturado": Decimal("0.00"),
                "ganancia_neta_total": Decimal("0.00"),
                "costo_total_mercaderia": Decimal("0.00"),
                "cantidad_transacciones": 0,
                "ticket_promedio": Decimal("0.00")
            }

        total_facturado = Decimal(str(resultado[0] or "0.00"))
        ganancia_neta_total = Decimal(str(resultado[1] or "0.00"))
        cantidad_transacciones = int(resultado[2] or 0)
        costo_total_mercaderia = total_facturado - ganancia_neta_total

        ticket_promedio = (
            total_facturado / cantidad_transacciones 
            if cantidad_transacciones > 0 
            else Decimal("0.00")
        )

        return {
            "total_facturado": total_facturado,
            "ganancia_neta_total": ganancia_neta_total,
            "costo_total_mercaderia": costo_total_mercaderia,
            "cantidad_transacciones": cantidad_transacciones,
            "ticket_promedio": round(ticket_promedio, 2)
        }

    @staticmethod
    def obtener_desglose_pagos(db: Session, fecha_inicio: datetime, fecha_fin: datetime) -> list[dict]:
        stmt = (
            select(
                VentaPago.medio_pago,
                func.coalesce(func.sum(VentaPago.monto), Decimal("0.00")).label("monto_total")
            )
            .join(Venta, VentaPago.venta_id == Venta.id)
            .where(
                and_(
                    Venta.fecha_venta >= fecha_inicio,
                    Venta.fecha_venta <= fecha_fin,
                    Venta.es_anulada == False
                )
            )
            .group_by(VentaPago.medio_pago)
        )

        resultados = db.execute(stmt).all()

        return [
            {"medio_pago": r[0], "monto_total": Decimal(str(r[1] or "0.00"))}
            for r in resultados
        ]

    @staticmethod
    def obtener_auditoria_anulaciones(db: Session, fecha_inicio: datetime, fecha_fin: datetime) -> dict:
        stmt = select(
            func.count(Venta.id).label("cantidad_anuladas"),
            func.coalesce(func.sum(Venta.total), Decimal("0.00")).label("monto_anulado")
        ).where(
            and_(
                Venta.fecha_venta >= fecha_inicio,
                Venta.fecha_venta <= fecha_fin,
                Venta.es_anulada == True
            )
        )

        resultado = db.execute(stmt).first()

        if not resultado:
            return {
                "cantidad_ventas_anuladas": 0,
                "monto_total_anulado": Decimal("0.00")
            }

        return {
            "cantidad_ventas_anuladas": int(resultado[0] or 0),
            "monto_total_anulado": Decimal(str(resultado[1] or "0.00"))
        }