from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.repositories.caja_repository import CajaRepository
from src.schemas.caja_schema import CajaCreate, CajaClose  
from src.models.caja import Caja
from typing import Optional
from datetime import date

class CajaService:

    @staticmethod
    def abrir_caja(db: Session, caja_in: CajaCreate, usuario_id: int):
        # 🔍 Validamos si ESTE usuario ya tiene un turno abierto
        caja_existente = CajaRepository.obtener_activa_por_usuario(db, usuario_id=usuario_id)
        if caja_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya tenés un turno de caja abierto. Debés cerrarlo antes de abrir uno nuevo."
            )
        
        # Guardamos en la base de datos usando el repositorio
        nuevo_turno = CajaRepository.crear(db, caja_in, usuario_apertura_id=usuario_id)
        db.commit()
        db.refresh(nuevo_turno)
        return nuevo_turno

    @staticmethod
    def obtener_caja_activa_por_usuario(db: Session, usuario_id: int):
        """Busca la caja activa del usuario logueado o tira un 404 limpio."""
        caja_activa = CajaRepository.obtener_activa_por_usuario(db, usuario_id=usuario_id)
        if not caja_activa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No tenés ninguna caja activa en este momento."
            )
        return caja_activa

    @staticmethod
    def cerrar_caja(db: Session, caja_close: CajaClose, usuario_id: int):
        # Buscamos la caja abierta de este usuario para cerrarla
        caja_activa = CajaRepository.obtener_activa_por_usuario(db, usuario_id=usuario_id)
        if not caja_activa:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No tenés ninguna caja abierta en este momento para poder cerrar."
            )
        
        try:
            # Hacemos el arqueo matemático (Monto Inicial + Suma de Ventas)
            total_ventas = sum(Decimal(str(v.total)) for v in caja_activa.ventas)
            monto_inicial = Decimal(str(caja_activa.monto_inicial))
            
            # Impactamos los datos finales de cierre
            caja_activa.monto_final_estimado = monto_inicial + total_ventas
            caja_activa.monto_final_real = caja_close.monto_final_real
            caja_activa.fecha_cierre = datetime.now() 
            caja_activa.estado = "CERRADA"
            caja_activa.usuario_cierre_id = usuario_id 
            
            db.commit()
            db.refresh(caja_activa)
            return caja_activa
            
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def listar_historial_cajas(db: Session, skip: int = 0, limit: int = 500,
                               caja_id: Optional[int] = None,
                               nombre_operario: Optional[str] = None, 
                               fecha_desde: Optional[date] = None, 
                               fecha_hasta: Optional[date] = None):
        return CajaRepository.obtener_historial_filtrado(
            db=db, caja_id=caja_id, nombre_operario=nombre_operario, fecha_desde=fecha_desde, 
            fecha_hasta=fecha_hasta, skip=skip, limit=limit
        )