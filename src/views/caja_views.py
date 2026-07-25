from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.dependencies.auth import get_current_user
from src.dependencies.roles import RoleChecker
from src.models.usuario import Usuario

router_vistas_cajas = APIRouter(prefix="/vistas", tags=["Vistas HTML Cajas Admin"])
templates = Jinja2Templates(directory="templates")

solo_admin = RoleChecker(["ADMIN", "admin"])

@router_vistas_cajas.get("/cajas", response_class=HTMLResponse)
async def vista_gestion_cajas(
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    _ = Depends(solo_admin)
):
    return templates.TemplateResponse(request, "cajas/control.html", {"usuario": current_user})

@router_vistas_cajas.get("/cajas_apertura", response_class=HTMLResponse)
async def vista_apertura_caja(
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    _ = Depends(solo_admin)
):
    return templates.TemplateResponse(request, "cajas/apertura.html", {"usuario": current_user})