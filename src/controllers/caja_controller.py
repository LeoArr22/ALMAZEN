from fastapi import APIRouter, Depends, status, Query 
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.schemas.caja_schema import CajaCreate, CajaClose, CajaResponse
from src.services.caja_service import CajaService
from src.dependencies.auth import get_current_user       
from src.models.usuario import Usuario
from datetime import date
from typing import Optional

router = APIRouter(prefix="/cajas", tags=["Cajas"])

# 🔓 EL VENDEDOR ABRE SU PROPIA CAJA (Usa la cookie automática)
@router.post("/", response_model=CajaResponse, status_code=status.HTTP_201_CREATED)
def abrir_caja(
    caja_in: CajaCreate, 
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user) # 👈 Lee quién es por la cookie
):
    """Abre un nuevo turno de caja para el usuario autenticado."""
    return CajaService.abrir_caja(db, caja_in, usuario_id=current_user.id)

# 🔓 EL VENDEDOR REVISA SU PROPIA CAJA (Usa la cookie automática)
@router.get("/activa", response_model=CajaResponse)
@router.get("/activa/", response_model=CajaResponse)
def obtener_caja_activa(
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user) # 👈  Lee quién es por la cookie
):
    """Trae los datos del turno de caja activo para el usuario actual."""
    # Nota: Asegurate de que tu CajaService tenga este método implementado
    return CajaService.obtener_caja_activa_por_usuario(db, usuario_id=current_user.id)

# 🔓 EL VENDEDOR CIERRA SU PROPIA CAJA (Usa la cookie automática)
@router.put("/cerrar", response_model=CajaResponse)
def cerrar_caja(
    caja_close: CajaClose, 
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user) # 👈 Lee quién es por la cookie
):
    """Cierra el turno de caja activo del usuario actual."""
    return CajaService.cerrar_caja(db, caja_close, usuario_id=current_user.id)

# 🛡️ SOLO ADMIN: Historial global para auditoría con BÚSQUEDA AVANZADA
@router.get("/historial", response_model=list[CajaResponse])
def listar_historial_cajas(
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000),  # Subimos el tope a 1000 por si busca un mes entero
    caja_id: Optional[int] = Query(None, description="Buscar un ID de caja exacto"),
    fecha_desde: Optional[date] = Query(None, description="Fecha de inicio (YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha de fin (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Trae el historial filtrando directamente desde la base de datos."""
    return CajaService.listar_historial_cajas(
        db=db, skip=skip, limit=limit, 
        caja_id=caja_id, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta
    )