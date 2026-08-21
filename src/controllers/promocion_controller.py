from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.schemas.promocion_schema import PromocionCreate, PromocionResponse, PromocionUpdate
from src.services.promocion_service import PromocionService

# 🛡️ IMPORTACIONES DE SEGURIDAD Y ROLES
from src.dependencies.roles import RoleChecker
from src.models.usuario import Usuario

router = APIRouter(prefix="/promociones", tags=["Promociones"])
solo_admin = RoleChecker(["ADMIN", "admin"])

# 🛡️ PROTEGIDO: Solo el admin crea promociones
@router.post("/", response_model=PromocionResponse, status_code=status.HTTP_201_CREATED)
def crear_promocion(
    promo_in: PromocionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(solo_admin)
):
    """Crea una nueva promoción (por cantidad o combo)."""
    return PromocionService.crear_promocion(db, promo_in)

# 🔓 LIBRE: El vendedor necesita consultar las promociones activas
@router.get("/", response_model=list[PromocionResponse])
def listar_promociones(solo_activas: bool = True, db: Session = Depends(get_db)):
    """Lista las promociones registradas."""
    return PromocionService.listar_promociones(db, solo_activas)

# 🔓 LIBRE: Consulta individual de promoción
@router.get("/{promocion_id}", response_model=PromocionResponse)
def obtener_promocion(promocion_id: int, db: Session = Depends(get_db)):
    """Obtiene el detalle de una promoción específica."""
    return PromocionService.obtener_promocion(db, promocion_id)

# 🛡️ PROTEGIDO: Solo el admin edita promociones
@router.put("/{promocion_id}", response_model=PromocionResponse)
def actualizar_promocion(
    promocion_id: int,
    promo_in: PromocionUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(solo_admin)
):
    """Actualiza los datos o el estado activo de una promoción."""
    return PromocionService.modificar_promocion(db, promocion_id, promo_in)

# 🛡️ PROTEGIDO: Solo el admin borra promociones
@router.delete("/{promocion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_promocion(
    promocion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(solo_admin)
):
    """Elimina permanentemente una promoción."""
    return PromocionService.borrar_promocion(db, promocion_id)