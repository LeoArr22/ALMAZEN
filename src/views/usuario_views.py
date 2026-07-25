from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.dependencies.auth import get_current_user
from src.dependencies.roles import RoleChecker
from src.models.usuario import Usuario

router_vistas_usuarios = APIRouter(prefix="/vistas", tags=["Vistas HTML Usuarios"])
templates = Jinja2Templates(directory="templates")

solo_admin = RoleChecker(["ADMIN", "admin"])

@router_vistas_usuarios.get("/usuarios", response_class=HTMLResponse)
async def servir_vista_administrador_usuarios(
    request: Request, 
    current_user: Usuario = Depends(get_current_user),
    _ = Depends(solo_admin)
):
    return templates.TemplateResponse(request, "usuarios/administrador.html")