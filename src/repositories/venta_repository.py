from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func
from src.models.venta import Venta, VentaDetalle
from src.models.venta_pago import VentaPago
from datetime import datetime

class VentaRepository:

    @staticmethod
    def crear_cabecera(db: Session, total: Decimal, ganancia_total: Decimal, caja_id: int, usuario_id: int) -> Venta:
        """Crea el registro madre de la venta con los totales finales y la caja asociada."""
        db_venta = Venta(
            caja_id=caja_id,  
            usuario_id=usuario_id,
            fecha_venta=datetime.now(),
            total=total,
            ganancia_total=ganancia_total
        )
        db.add(db_venta)
        db.flush()  # El flush genera el ID de la venta sin cerrar la transacción
        return db_venta

    @staticmethod
    def crear_detalle(
        db: Session, 
        venta_id: int, 
        producto_id: int, 
        cantidad: Decimal, 
        precio_historico: Decimal, 
        costo_historico: Decimal
    ) -> VentaDetalle:
        """Inserta un renglón del carrito asociado a la venta madre con campos calculados."""
        # Calculamos los montos de forma exacta con Decimal
        subtotal = precio_historico * cantidad
        ganancia_item = (precio_historico - costo_historico) * cantidad

        db_detalle = VentaDetalle(
            venta_id=venta_id,
            producto_id=producto_id,
            cantidad=cantidad,
            precio_historico=precio_historico, 
            costo_historico=costo_historico,   
            subtotal=subtotal,                 
            ganancia_item=ganancia_item
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
        """Inserta un medio de pago asociado a la venta madre."""
        db_pago = VentaPago(
            venta_id=venta_id,
            medio_pago=medio_pago,
            monto=monto
        )
        db.add(db_pago)
        return db_pago

    @staticmethod
    def obtener_por_id(db: Session, venta_id: int) -> Venta | None:
        """Busca una venta específica y trae sus detalles y pagos de un solo viaje."""
        return db.query(Venta).options(
            joinedload(Venta.detalles),
            joinedload(Venta.pagos)
        ).filter(Venta.id == venta_id).first()
        
    @staticmethod
    def obtener_por_vendedor(db: Session, usuario_id: int, skip: int = 0, limit: int = 100) -> list[Venta]:
        """Consulta en la base de datos las ventas asociadas a un vendedor específico."""
        return (
            db.query(Venta)
            .options(
                joinedload(Venta.detalles),
                joinedload(Venta.pagos)
            )
            .filter(Venta.usuario_id == usuario_id)
            .order_by(Venta.fecha_venta.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def obtener_todas(
        db: Session, 
        skip: int = 0, 
        limit: int = 100, 
        caja_id: Optional[int] = None, 
        fecha: Optional[str] = None
    ) -> list[Venta]:
        """Trae el historial de ventas aplicando filtros dinámicos desde la BD."""
        query = db.query(Venta).options(
            joinedload(Venta.detalles),
            joinedload(Venta.pagos)
        )
        
        filtros = []
        
        # Filtro por Caja ID
        if caja_id is not None:
            filtros.append(Venta.caja_id == caja_id)
            
        # Filtro por Fecha (comparamos solo la parte YYYY-MM-DD)
        if fecha:
            filtros.append(func.date(Venta.fecha_venta) == fecha)
            
        if filtros:
            query = query.filter(and_(*filtros))
        
        return query.order_by(Venta.fecha_venta.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def eliminar(db: Session, db_venta: Venta) -> None:
        """Elimina una venta y sus detalles/pagos por cascada."""
        db.delete(db_venta)
        db.commit()