from decimal import Decimal
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, and_
from src.models.venta import Venta, VentaDetalle
from src.models.venta_pago import VentaPago
from datetime import datetime

class VentaRepository:

    @staticmethod
    def crear_cabecera(db: Session, total: Decimal, ganancia_total: Decimal, caja_id: int, usuario_id: int) -> Venta:
        db_venta = Venta(
            caja_id=caja_id,  
            usuario_id=usuario_id,
            fecha_venta=datetime.now(),
            total=total,
            ganancia_total=ganancia_total
        )
        db.add(db_venta)
        db.flush()
        return db_venta

    @staticmethod
    def crear_detalle(
        db: Session, 
        venta_id: int, 
        producto_id: int, 
        cantidad: Decimal, 
        precio_historico: Decimal, 
        costo_historico: Decimal,
        promocion_aplicada: Optional[str] = None
    ) -> VentaDetalle:
        subtotal = precio_historico * cantidad
        ganancia_item = (precio_historico - costo_historico) * cantidad

        db_detalle = VentaDetalle(
            venta_id=venta_id,
            producto_id=producto_id,
            cantidad=cantidad,
            precio_historico=precio_historico, 
            costo_historico=costo_historico,   
            subtotal=subtotal,                 
            ganancia_item=ganancia_item,
            promocion_aplicada=promocion_aplicada
        )
        db.add(db_detalle)
        return db_detalle

    @staticmethod
    def crear_pago(
        db: Session, 
        venta_id: int, 
        medio_pago: str, 
        monto: Decimal
    ) -> VentaPago:
        db_pago = VentaPago(
            venta_id=venta_id,
            medio_pago=medio_pago,
            monto=monto
        )
        db.add(db_pago)
        return db_pago

    @staticmethod
    def obtener_por_id(db: Session, venta_id: int) -> Optional[Venta]:
        stmt = (
            select(Venta)
            .options(
                joinedload(Venta.detalles).joinedload(VentaDetalle.producto),
                joinedload(Venta.pagos),
                joinedload(Venta.vendedor)
            )
            .where(Venta.id == venta_id)
        )
        return db.scalars(stmt).first()

    @staticmethod
    def obtener_todas(
        db: Session, 
        skip: int = 0, 
        limit: int = 100, 
        caja_id: Optional[int] = None, 
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> List[Venta]:
        stmt = select(Venta).options(
            joinedload(Venta.detalles).joinedload(VentaDetalle.producto),
            joinedload(Venta.pagos),
            joinedload(Venta.vendedor)
        )
        
        filtros = []
        if caja_id is not None:
            filtros.append(Venta.caja_id == caja_id)
        if fecha_desde:
            filtros.append(Venta.fecha_venta >= fecha_desde)
        if fecha_hasta:
            filtros.append(Venta.fecha_venta <= fecha_hasta)
            
        if filtros:
            stmt = stmt.where(and_(*filtros))
            
        stmt = stmt.order_by(Venta.fecha_venta.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())
        
    @staticmethod
    def obtener_por_vendedor(db: Session, usuario_id: int, skip: int = 0, limit: int = 100) -> list[Venta]:
        stmt = (
            select(Venta)
            .options(
                joinedload(Venta.detalles).joinedload(VentaDetalle.producto),
                joinedload(Venta.pagos),
                joinedload(Venta.vendedor)
            )
            .where(Venta.usuario_id == usuario_id)
            .order_by(Venta.fecha_venta.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())