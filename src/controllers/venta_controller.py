from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.models.usuario import Usuario
from src.dependencies.auth import get_current_user
from src.schemas.venta_schema import VentaCreate, VentaResponse
from src.services.venta_service import VentaService

router = APIRouter(prefix="/ventas", tags=["Ventas"])

@router.post("/", response_model=VentaResponse, status_code=status.HTTP_201_CREATED)
def registrar_venta(venta_in: VentaCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    """Registra una nueva venta, descuenta stock y congela precios históricos."""
    return VentaService.registrar_venta(db, venta_in, usuario_id=current_user.id)

@router.get("/{venta_id}", response_model=VentaResponse)
def obtener_venta(venta_id: int, db: Session = Depends(get_db)):
    """Busca una venta específica por su ID junto con todos sus renglones."""
    return VentaService.obtener_venta(db, venta_id)

@router.get("/", response_model=list[VentaResponse])
def listar_ventas(
    skip: int = 0, 
    limit: int = 100, 
    caja_id: Optional[int] = None,
    fecha: Optional[str] = None,
    db: Session = Depends(get_db)
    ):
    """Trae el historial de ventas filtrado y paginado desde el motor de BD."""
    return VentaService.listar_ventas(db, skip, limit, caja_id, fecha)

@router.delete("/{venta_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancelar_venta(venta_id: int, db: Session = Depends(get_db)):
    """Cancela una venta y devuelve el stock correspondiente a los productos."""
    VentaService.cancelar_venta(db, venta_id)
    return None
