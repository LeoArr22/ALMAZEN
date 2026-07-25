from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.dependencies.auth import get_current_user
from src.dependencies.roles import RoleChecker
from src.models.usuario import Usuario

router_vistas_productos = APIRouter(prefix="/vistas", tags=["Vistas HTML Productos"])
templates = Jinja2Templates(directory="templates")

solo_admin = RoleChecker(["ADMIN", "admin"])

@router_vistas_productos.get("/productos/carga", response_class=HTMLResponse)
async def servir_vista_carga_productos(
    request: Request, 
    current_user: Usuario = Depends(get_current_user),
    _ = Depends(solo_admin)
):
    return templates.TemplateResponse(request, "productos/carga.html")

@router_vistas_productos.get("/productos/buscar_editar", response_class=HTMLResponse)
async def servir_vista_buscar_editar_productos(
    request: Request, 
    current_user: Usuario = Depends(get_current_user),
    _ = Depends(solo_admin)
):
    return templates.TemplateResponse(request, "productos/buscar_editar.html")