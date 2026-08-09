# src/controllers/libro_controller.py
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.models.usuario import Usuario
from src.schemas.libro_schema import LibroDiarioResponse
from src.services.libro_service import LibroService
from src.dependencies.roles import RoleChecker

router = APIRouter(prefix="/libro-diario", tags=["Libro Diario / Reportes Contables"])
solo_admin = RoleChecker(["ADMIN", "admin"])

@router.get("/", response_model=LibroDiarioResponse, status_code=status.HTTP_200_OK)
def consultar_libro_diario(
    periodo: str = Query("dia", description="Períodos disponibles: 'dia', 'semana', 'mes', 'personalizado'"),
    fecha_ref: Optional[date] = Query(None, description="Fecha base para la consulta (Por defecto: Hoy)"),
    fecha_inicio_custom: Optional[date] = Query(None, description="Requerido si periodo='personalizado'"),
    fecha_fin_custom: Optional[date] = Query(None, description="Requerido si periodo='personalizado'"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(solo_admin) # Solo ADMIN puede ver balances
):
    """
    Retorna el resumen contable (facturación, costos, ganancias y medios de pago).
    Por defecto devuelve el día de hoy, pero permite filtrar por semana, mes o rango personalizado.
    """
    return LibroService.obtener_libro_diario(
        db=db,
        periodo=periodo,
        fecha_ref=fecha_ref,
        fecha_inicio_custom=fecha_inicio_custom,
        fecha_fin_custom=fecha_fin_custom
    )