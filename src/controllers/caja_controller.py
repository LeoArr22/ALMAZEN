from fastapi import APIRouter, Depends, status, Query 
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.schemas.caja_schema import CajaCreate, CajaClose, CajaResponse
from src.services.caja_service import CajaService
from src.dependencies.auth import get_current_user       
from src.models.usuario import Usuario

router = APIRouter(prefix="/cajas", tags=["Cajas"])

@router.post("/", response_model=CajaResponse, status_code=status.HTTP_201_CREATED)
def abrir_caja(caja_in: CajaCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    """
    Abre un nuevo turno de caja con un monto inicial, 
    validando que no haya otra abierta y registrando el usuario que la abre.
    """
    # Le pasamos el ID del usuario autenticado de forma segura al servicio
    return CajaService.abrir_caja(db, caja_in, usuario_id=current_user.id)

@router.get("/activa", response_model=CajaResponse)
def obtener_caja_activa(db: Session = Depends(get_db)):
    """Trae los datos del turno de caja activo calculando el total acumulado en tiempo real."""
    return CajaService.obtener_caja_activa(db)

@router.put("/cerrar", response_model=CajaResponse)
def cerrar_caja(caja_close: CajaClose, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    """
    Cierra el turno de caja activo registrando el dinero real contado en el local,
    haciendo el balance automático y guardando el usuario que realiza el cierre.
    """
    # Le pasamos el carrito/datos de cierre y el ID del usuario que lo ejecuta
    return CajaService.cerrar_caja(db, caja_close, usuario_id=current_user.id)

@router.get("/historial", response_model=list[CajaResponse])
def listar_historial_cajas(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"), 
    limit: int = Query(100, ge=1, le=500, description="Máximo de registros a retornar"), 
    db: Session = Depends(get_db)
):
    """Trae el historial completo de turnos de caja para auditoría."""
    return CajaService.listar_historial_cajas(db, skip, limit)

# Mantenemos esta ruta al final de todo para evitar conflictos dinámicos
@router.get("/{caja_id}", response_model=CajaResponse)
def obtener_caja_por_id(caja_id: int, db: Session = Depends(get_db)):
    """Busca un turno de caja específico por su ID."""
    return CajaService.obtener_caja(db, caja_id)