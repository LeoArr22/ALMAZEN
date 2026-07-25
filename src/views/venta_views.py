from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.models.usuario import Usuario
from src.dependencies.auth import get_current_user

router_vistas_ventas = APIRouter(prefix="/vistas", tags=["Vistas HTML Ventas"])
templates = Jinja2Templates(directory="templates")

@router_vistas_ventas.get("/ventas/pos", response_class=HTMLResponse)
async def servir_punto_de_venta(request: Request, current_user: Usuario = Depends(get_current_user)):
    return templates.TemplateResponse(request, "ventas/pos.html")

@router_vistas_ventas.get("/ventas/historial", response_class=HTMLResponse)
async def servir_historial_ventas(request: Request, current_user: Usuario = Depends(get_current_user)):
    return templates.TemplateResponse(request, "ventas/historial.html")