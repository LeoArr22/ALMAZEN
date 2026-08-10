# src/views/libro_views.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.models.usuario import Usuario
from src.dependencies.auth import get_current_user

router_vistas_libro = APIRouter(prefix="/vistas", tags=["Vistas HTML Libro Diario"])
templates = Jinja2Templates(directory="templates")

@router_vistas_libro.get("/libro/diario", response_class=HTMLResponse)
async def servir_libro_diario(request: Request, current_user: Usuario = Depends(get_current_user)):
    return templates.TemplateResponse(request, "libro/diario.html")

@router_vistas_libro.get("/libro/general", response_class=HTMLResponse)
async def servir_libro_general(request: Request, current_user: Usuario = Depends(get_current_user)):
    return templates.TemplateResponse(request, "libro/general.html")