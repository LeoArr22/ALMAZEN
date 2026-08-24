from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.models.usuario import Usuario
from src.dependencies.auth import get_current_user
from src.dependencies.roles import RoleChecker
from src.schemas.caja_schema import CajaCreate, CajaClose, CajaResponse
from src.services.caja_service import CajaService

router = APIRouter(prefix="/cajas", tags=["Cajas"])
solo_admin = RoleChecker(["ADMIN", "admin"])

@router.post("/", response_model=CajaResponse, status_code=status.HTTP_201_CREATED)
def abrir_caja(
    caja_in: CajaCreate, 
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user)
):
    """Abre un nuevo turno de caja asociando al usuario logueado como usuario de apertura."""
    return CajaService.abrir_caja(db, caja_in, usuario_id=current_user.id)

@router.get("/activa", response_model=CajaResponse)
def obtener_caja_activa(
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user)
):
    """Consulta la caja abierta del usuario actual junto con el desglose dinámico en tiempo real."""
    return CajaService.obtener_caja_activa_por_usuario(db, usuario_id=current_user.id)

@router.post("/cerrar", response_model=CajaResponse)
def cerrar_caja(
    caja_close: CajaClose, 
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user)
):
    """Cierra la caja activa del usuario logueado calculando el esperado en efectivo."""
    return CajaService.cerrar_caja(db, caja_close, usuario_id=current_user.id)

@router.get("/historial", response_model=List[CajaResponse])
def listar_historial_cajas(
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1),
    caja_id: Optional[int] = Query(None),
    nombre_operario: Optional[str] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(solo_admin)
):
    """Obtiene el historial con filtros completos y auditoría de métodos de pago/usuarios."""
    return CajaService.listar_historial_cajas(
        db=db,
        skip=skip,
        limit=limit,
        caja_id=caja_id,
        nombre_operario=nombre_operario,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )