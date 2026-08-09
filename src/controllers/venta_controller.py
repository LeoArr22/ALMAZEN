from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.models.usuario import Usuario
from src.dependencies.auth import get_current_user
from src.schemas.venta_schema import VentaCreate, VentaResponse
from src.services.venta_service import VentaService

# 🛡️ IMPORTACIONES DE SEGURIDAD Y ROLES
from src.dependencies.roles import RoleChecker

router = APIRouter(prefix="/ventas", tags=["Ventas"])
solo_admin = RoleChecker(["ADMIN", "admin"])

# 🔓 LIBRE (CON LOGIN): El vendedor procesa la venta en caliente con los clientes
@router.post("/", response_model=VentaResponse, status_code=status.HTTP_201_CREATED)
def registrar_venta(venta_in: VentaCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    """Registra una nueva venta, descuenta stock y congela precios históricos."""
    return VentaService.registrar_venta(db, venta_in, usuario_id=current_user.id)

# 🔓 LIBRE: Útil si el vendedor necesita reimprimir un ticket o validar la venta recién hecha
@router.get("/{venta_id}", response_model=VentaResponse)
def obtener_venta(venta_id: int, db: Session = Depends(get_db)):
    """Busca una venta específica por su ID junto con todos sus renglones."""
    return VentaService.obtener_venta(db, venta_id)

# 🛡️ PROTEGIDO: Listados históricos globales y balances generales quedan bajo llave
@router.get("/", response_model=list[VentaResponse])
def listar_ventas(
    skip: int = 0, 
    limit: int = 100, 
    caja_id: Optional[int] = None,
    fecha: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(solo_admin)  # 👈 Inyección de rol
):
    """Trae el historial de ventas filtrado y paginado desde el motor de BD."""
    return VentaService.listar_ventas(db, skip, limit, caja_id, fecha)

# 🛡️ PROTEGIDO: Solo un ADMIN puede anular una venta, lo que devuelve el stock y marca la venta como anulada
@router.post("/{venta_id}/anular", response_model=VentaResponse)
def anular_venta(
    venta_id: int, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(solo_admin) # Protegido solo para ADMIN
):
    """Anula la venta, devuelve el stock y la marca como anulada."""
    return VentaService.cancelar_venta(db, venta_id)