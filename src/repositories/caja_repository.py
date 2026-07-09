from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.models.caja import Caja
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
            .filter((Caja.usuario_apertura_id == usuario_id) | (Caja.usuario_cierre_id == usuario_id))
            .order_by(Caja.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def obtener_activa(db: Session) -> Optional[Caja]:
        return db.scalars(select(Caja).filter(Caja.estado == "ABIERTA")).first()

    @staticmethod
    def obtener_por_id(db: Session, caja_id: int) -> Optional[Caja]:
        return db.query(Caja).filter(Caja.id == caja_id).first()

    @staticmethod
    def obtener_todas(db: Session, skip: int = 0, limit: int = 100) -> list[Caja]:
        return db.query(Caja).order_by(Caja.id.desc()).offset(skip).limit(limit).all()