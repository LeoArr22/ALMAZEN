from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Importaciones de tu modelo y seguridad
from src.models.usuario import Usuario
from src.dependencies.auth import get_current_user

# Usamos el prefijo /vistas para heredar la lógica que ya armaste en tu JavaScript
router_vistas_productos = APIRouter(prefix="/vistas", tags=["Vistas HTML Productos"])
templates = Jinja2Templates(directory="templates")

@router_vistas_productos.get("/productos/carga", response_class=HTMLResponse)
async def servir_vista_carga_productos(request: Request, current_user: Usuario = Depends(get_current_user)):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    return templates.TemplateResponse("productos/carga.html", {"request": request})

@router_vistas_productos.get("/productos/buscar_editar", response_class=HTMLResponse)
async def servir_vista_buscar_editar_productos(request: Request, current_user: Usuario = Depends(get_current_user)):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    return templates.TemplateResponse("productos/buscar_editar.html", {"request": request})