from fastapi import APIRouter, Depends, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.schemas.usuario_schema import UsuarioCreate, UsuarioResponse, TokenResponse
from src.services.usuario_service import UsuarioService
from src.dependencies.auth import get_current_user
from src.dependencies.roles import RoleChecker
from src.models.usuario import Usuario

router = APIRouter(prefix="/usuarios", tags=["Usuarios & Autenticación"])
solo_admin = RoleChecker(["ADMIN", "admin"])

# 🛡️ PROTEGIDO: Solo administradores pueden crear nuevos usuarios en AlmaZen
@router.post("/registrar", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def registrar_usuario(
    usuario_in: UsuarioCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(solo_admin)
):
    """Registra un nuevo usuario en el sistema aplicando hasheo."""
    return UsuarioService.registrar_usuario(db, usuario_in)

# 🔓 COMPLETO PÚBLICO: El login debe ser abierto para que todos inicien sesión
@router.post("/login", response_model=TokenResponse)
def login(
    response: Response,  # 👈 Inyectamos la Response de FastAPI
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """Autentica al usuario mediante username y password y setea la cookie HttpOnly."""
    
    # 1. Llamamos a tu servicio tal cual está hoy
    token_dto = UsuarioService.autenticar_usuario(db, username=form_data.username, password=form_data.password)
    
    # 2. Seteamos la cookie HttpOnly directamente en la respuesta HTTP
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token_dto.access_token}", # O el token limpio según prefieras
        httponly=True,  # 🔒 Impide lectura desde JS (protección XSS)
        samesite="lax",  # 🛡️ Protección contra CSRF
        path="/"         # Disponible para todas las rutas del sistema
    )
    
    # 3. Retornamos el mismo DTO (el cliente sigue recibiendo el JSON si lo necesita)
    return token_dto

# 🔓 LIBRE (CON LOGIN): Cualquiera puede ver quién está autenticado en su terminal
@router.get("/me", response_model=UsuarioResponse)
def obtener_perfil_actual(current_user: Usuario = Depends(get_current_user)):
    """Retorna los datos del usuario dueño del JWT provisto en los headers."""
    return current_user