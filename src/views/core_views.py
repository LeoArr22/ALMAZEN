from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.models.usuario import Usuario
from src.dependencies.auth import get_current_user

router_core = APIRouter(tags=["Vistas Core UI"])
templates = Jinja2Templates(directory="templates")

@router_core.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login/login.html")

@router_core.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request, current_user: Usuario = Depends(get_current_user)):
    if current_user.role == "ADMIN":
        return templates.TemplateResponse(request, "dashboard.html", {"usuario": current_user})
    else:
        return templates.TemplateResponse(request, "panel_vendedor.html", {"usuario": current_user})