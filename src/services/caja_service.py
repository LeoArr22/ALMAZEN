from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.repositories.caja_repository import CajaRepository
from src.schemas.caja_schema import CajaCreate, CajaClose  
from src.models.caja import Caja

class CajaService:

    @staticmethod
    def abrir_caja(db: Session, caja_in: CajaCreate, usuario_id: int) -> Caja:
        """
        Abre un nuevo turno de caja validando que no haya otra activa
        y controlando la persistencia de forma atómica en la capa de negocio.
        """
        caja_activa = CajaRepository.obtener_activa(db)
        if caja_activa:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede abrir una nueva caja porque ya existe un turno activo (Caja Abierta)."
            )
        
        try:
            # Invoca al repositorio para preparar la inserción
            nueva_caja = CajaRepository.crear(db, caja_in, usuario_id)
            
            # El servicio decide confirmar la transacción de forma definitiva
            db.commit()
            db.refresh(nueva_caja)
            return nueva_caja
            
        except Exception as e:
            # Si ocurre un error inesperado, deshace cualquier cambio en la sesión
            db.rollback()
            raise e

    @staticmethod
    def obtener_caja(db: Session, caja_id: int) -> Caja:
        """Busca una caja por su ID y lanza 404 si no existe."""
        caja = CajaRepository.obtener_por_id(db, caja_id)
        if not caja:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Turno de caja con ID {caja_id} no encontrado."
            )
        return caja

    @staticmethod
    def obtener_cajas_por_usuario(db: Session, usuario_id: int, skip: int = 0, limit: int = 100) -> list[Caja]:
        """
        Recupera el historial de turnos de caja filtrado por el identificador del usuario.
        Pasa la solicitud directamente al repositorio aplicando la paginación correspondiente.
        """
        return CajaRepository.obtener_por_usuario(db, usuario_id, skip, limit)

    @staticmethod
    def obtener_caja_activa(db: Session) -> Caja:
        """Busca la caja abierta actual y calcula su total acumulado en tiempo real."""
        caja_activa = CajaRepository.obtener_activa(db)
        if not caja_activa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Actualmente no hay ninguna caja abierta en el sistema."
            )
        
        # Calculamos el acumulado sumando el monto inicial + las ventas reales
        total_ventas = sum(Decimal(str(v.total)) for v in caja_activa.ventas)
        monto_inicial = Decimal(str(caja_activa.monto_inicial))
        
        caja_activa.monto_final_estimado = monto_inicial + total_ventas
        
        # Persistimos el estimado actual por si se consulta desde la API
        db.commit()
        db.refresh(caja_activa)
        
        return caja_activa

    @staticmethod
    def cerrar_caja(db: Session, caja_close: CajaClose, usuario_id: int) -> Caja:
        """
        Cierra el turno de caja activo, calcula el balance transaccional
        e ingresa el monto real contado bajo la auditoría del usuario actual.
        """
        # 1. Buscamos si efectivamente hay una caja abierta para cerrar
        caja_activa = CajaRepository.obtener_activa(db)
        if not caja_activa:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay ninguna caja abierta en este momento para poder cerrar."
            )
        
        try:
            # 2. Hacemos el arqueo matemático (Monto Inicial + Suma de Ventas)
            total_ventas = sum(Decimal(str(v.total)) for v in caja_activa.ventas)
            monto_inicial = Decimal(str(caja_activa.monto_inicial))
            
            # 3. Impactamos los datos finales de cierre y auditoría
            caja_activa.monto_final_estimado = monto_inicial + total_ventas
            caja_activa.monto_final_real = caja_close.monto_final_real
            caja_activa.fecha_cierre = datetime.now() 
            caja_activa.estado = "CERRADA"
            
            # Asignamos el ID del usuario que ejecuta el cierre
            caja_activa.usuario_cierre_id = usuario_id 
            
            # 4. El servicio controla la transacción de forma atómica en el disco
            db.commit()
            db.refresh(caja_activa)
            return caja_activa
            
        except Exception as e:
            # Si algo falla calculando o guardando, volvemos atrás limpiamente
            db.rollback()
            raise e

    @staticmethod
    def listar_historial_cajas(db: Session, skip: int = 0, limit: int = 100) -> list[Caja]:
        """Devuelve el historial de turnos de caja para auditoría."""
        return CajaRepository.obtener_todas(db, skip, limit)