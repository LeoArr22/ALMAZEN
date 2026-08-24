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
        """
        Prepara e inserta el nuevo turno de caja en la sesión de SQLAlchemy.
        Delega el commit y control transaccional a la capa de servicio.
        """
        nuevo_turno = Caja(
            **caja_in.model_dump(),
            usuario_apertura_id=usuario_apertura_id,
            estado="ABIERTA"
        )
        db.add(nuevo_turno)
        db.flush()  # Genera el ID en memoria dentro de la transacción activa
        return nuevo_turno
    
    @staticmethod
    def obtener_por_usuario(db: Session, usuario_id: int, skip: int = 0, limit: int = 100) -> list[Caja]:
        """
        Consulta y retorna el historial de turnos de caja en los que un usuario específico
        estuvo involucrado, ya sea en la apertura o en el cierre del turno.
        """
        return (
            db.query(Caja)
            .options(
                joinedload(Caja.usuario_apertura),
                joinedload(Caja.usuario_cierre),
                joinedload(Caja.ventas).joinedload(Venta.pagos)
            )
            .filter(or_(Caja.usuario_apertura_id == usuario_id, Caja.usuario_cierre_id == usuario_id))
            .order_by(Caja.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def obtener_activa(db: Session) -> Optional[Caja]:
        return (
            db.query(Caja)
            .options(
                joinedload(Caja.usuario_apertura),
                joinedload(Caja.usuario_cierre),
                joinedload(Caja.ventas).joinedload(Venta.pagos)
            )
            .filter(Caja.estado == "ABIERTA")
            .first()
        )

    @staticmethod
    def obtener_por_id(db: Session, caja_id: int) -> Optional[Caja]:
        return (
            db.query(Caja)
            .options(
                joinedload(Caja.usuario_apertura),
                joinedload(Caja.usuario_cierre),
                joinedload(Caja.ventas).joinedload(Venta.pagos)
            )
            .filter(Caja.id == caja_id)
            .first()
        )

    @staticmethod
    def obtener_todas(db: Session, skip: int = 0, limit: int = 100) -> list[Caja]:
        return (
            db.query(Caja)
            .options(
                joinedload(Caja.usuario_apertura),
                joinedload(Caja.usuario_cierre),
                joinedload(Caja.ventas).joinedload(Venta.pagos)
            )
            .order_by(Caja.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    @staticmethod
    def obtener_activa_por_usuario(db: Session, usuario_id: int) -> Optional[Caja]:
        """
        Busca si el usuario en cuestión tiene un turno de caja abierto actualmente.
        """
        return (
            db.query(Caja)
            .options(
                joinedload(Caja.usuario_apertura),
                joinedload(Caja.usuario_cierre),
                joinedload(Caja.ventas).joinedload(Venta.pagos)
            )
            .filter(
                Caja.usuario_apertura_id == usuario_id,
                Caja.estado == "ABIERTA"
            )
            .first()
        )
        
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
        
        query = (
            db.query(Caja)
            .options(
                joinedload(Caja.usuario_apertura),
                joinedload(Caja.usuario_cierre),
                joinedload(Caja.ventas).joinedload(Venta.pagos)
            )
            .join(Caja.usuario_apertura)
        )
        
        if caja_id:
            query = query.filter(Caja.id == caja_id)
        
        if nombre_operario:
            query = query.filter(Usuario.username.ilike(f"%{nombre_operario}%"))
        
        if fecha_desde:
            query = query.filter(Caja.fecha_apertura >= fecha_desde)
        if fecha_hasta:
            query = query.filter(Caja.fecha_apertura <= fecha_hasta)
            
        return query.order_by(Caja.id.desc()).offset(skip).limit(limit).all()