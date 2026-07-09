from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.schemas.usuario_schema import UsuarioCreate, UsuarioResponse, TokenResponse
from src.services.usuario_service import UsuarioService
from src.dependencies.auth import get_current_user
from src.dependencies.roles import RoleChecker
from src.models.usuario import Usuario

router = APIRouter(prefix="/usuarios", tags=["Usuarios & Autenticación"])

# Definimos el verificador local para endpoints específicos
solo_admin = RoleChecker(["ADMIN", "admin"])

# ==========================================
# 1. ENDPOINT: REGISTRO DE USUARIOS (PROTEGIDO)
# ==========================================
@router.post("/registrar", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def registrar_usuario(
    usuario_in: UsuarioCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(solo_admin)  # 🌟 Solo administradores pueden crear usuarios
):
    """
    Registra un nuevo usuario en el sistema. 
    Transforma la contraseña recibida en un hash seguro antes de guardarla.
    """
    return UsuarioService.registrar_usuario(db, usuario_in)


# ==========================================
# 2. ENDPOINT: LOGIN (TOTALMENTE PÚBLICO Y COMPATIBLE CON EL CANDADO)
# ==========================================
@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """
    Autentica al usuario mediante username y password (enviados como Form Data).
    Retorna un JSON Web Token (JWT) válido si las credenciales coinciden.
    Compatible con el botón 'Authorize' (candado) de Swagger.
    """
    return UsuarioService.autenticar_usuario(
        db, 
        username=form_data.username, 
        password=form_data.password
    )


# ==========================================
# 3. ENDPOINT: PERFIL ACTUAL (PROTEGIDO)
# ==========================================
@router.get("/me", response_model=UsuarioResponse)
def obtener_perfil_actual(current_user: Usuario = Depends(get_current_user)):
    """
    Endpoint de prueba para verificar si el token actual es válido y ver los datos del usuario logueado.
    """
    return current_user