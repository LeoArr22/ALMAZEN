from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, or_
from src.models.caja import Caja
from src.models.venta import Venta
from src.models.usuario import Usuario
from src.schemas.caja_schema import CajaCreate

class CajaRepository:

    @staticmethod
    def crear(db: Session, caja_in: CajaCreate, usuario_apertura_id: int) -> Caja:
        nuevo_turno = Caja(
            **caja_in.model_dump(),
            usuario_apertura_id=usuario_apertura_id,
            estado="ABIERTA"
        )
        db.add(nuevo_turno)
        db.flush()
        return nuevo_turno
    
    @staticmethod
    def obtener_por_usuario(db: Session, usuario_id: int, skip: int = 0, limit: int = 100) -> list[Caja]:
        stmt = (
            select(Caja)
            .options(
                joinedload(Caja.usuario_apertura),
                joinedload(Caja.usuario_cierre),
                joinedload(Caja.ventas).joinedload(Venta.pagos)
            )
            .where(or_(Caja.usuario_apertura_id == usuario_id, Caja.usuario_cierre_id == usuario_id))
            .order_by(Caja.id.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def obtener_activa(db: Session) -> Optional[Caja]:
        stmt = (
            select(Caja)
            .options(
                joinedload(Caja.usuario_apertura),
                joinedload(Caja.usuario_cierre),
                joinedload(Caja.ventas).joinedload(Venta.pagos)
            )
            .where(Caja.estado == "ABIERTA")
        )
        return db.scalars(stmt).first()

    @staticmethod
    def obtener_por_id(db: Session, caja_id: int) -> Optional[Caja]:
        stmt = (
            select(Caja)
            .options(
                joinedload(Caja.usuario_apertura),
                joinedload(Caja.usuario_cierre),
                joinedload(Caja.ventas).joinedload(Venta.pagos)
            )
            .where(Caja.id == caja_id)
        )
        return db.scalars(stmt).first()

    @staticmethod
    def obtener_todas(db: Session, skip: int = 0, limit: int = 100) -> list[Caja]:
        stmt = (
            select(Caja)
            .options(
                joinedload(Caja.usuario_apertura),
                joinedload(Caja.usuario_cierre),
                joinedload(Caja.ventas).joinedload(Venta.pagos)
            )
            .order_by(Caja.id.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())
    
    @staticmethod
    def obtener_activa_por_usuario(db: Session, usuario_id: int) -> Optional[Caja]:
        stmt = (
            select(Caja)
            .options(
                joinedload(Caja.usuario_apertura),
                joinedload(Caja.usuario_cierre),
                joinedload(Caja.ventas).joinedload(Venta.pagos)
            )
            .where(
                Caja.usuario_apertura_id == usuario_id,
                Caja.estado == "ABIERTA"
            )
        )
        return db.scalars(stmt).first()
        
    @staticmethod
    def obtener_historial_filtrado(
        db: Session, 
        caja_id: Optional[int] = None,
        nombre_operario: Optional[str] = None,
        fecha_desde: Optional[date] = None, 
        fecha_hasta: Optional[date] = None, 
        skip: int = 0, 
        limit: int = 500
    ) -> list[Caja]:
        
        stmt = (
            select(Caja)
            .options(
                joinedload(Caja.usuario_apertura),
                joinedload(Caja.usuario_cierre),
                joinedload(Caja.ventas).joinedload(Venta.pagos)
            )
            .join(Caja.usuario_apertura)
        )
        
        if caja_id:
            stmt = stmt.where(Caja.id == caja_id)
        
        if nombre_operario:
            stmt = stmt.where(Usuario.username.ilike(f"%{nombre_operario}%"))
        
        if fecha_desde:
            stmt = stmt.where(Caja.fecha_apertura >= fecha_desde)
        if fecha_hasta:
            stmt = stmt.where(Caja.fecha_apertura <= fecha_hasta)
            
        stmt = stmt.order_by(Caja.id.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())