from typing import List
from fastapi import APIRouter, Depends, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.schemas.usuario_schema import UsuarioCreate, UsuarioUpdate, UsuarioResponse, TokenResponse
from src.services.usuario_service import UsuarioService
from src.dependencies.auth import get_current_user
from src.dependencies.roles import RoleChecker
from src.models.usuario import Usuario

router = APIRouter(prefix="/usuarios", tags=["Usuarios & Autenticación"])
solo_admin = RoleChecker(["ADMIN", "admin"])

@router.post("/registrar", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def registrar_usuario(
    usuario_in: UsuarioCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(solo_admin)
):
    return UsuarioService.registrar_usuario(db, usuario_in)

@router.get("/", response_model=List[UsuarioResponse])
def listar_usuarios(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(solo_admin)
):
    return UsuarioService.listar_usuarios(db)

@router.put("/{usuario_id}", response_model=UsuarioResponse)
def actualizar_usuario(
    usuario_id: int,
    usuario_in: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(solo_admin)
):
    return UsuarioService.actualizar_usuario(db, usuario_id, usuario_in)

@router.patch("/{usuario_id}/estado", response_model=UsuarioResponse)
def alternar_estado_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(solo_admin)
):
    return UsuarioService.alternar_estado_usuario(db, usuario_id)

@router.post("/login", response_model=TokenResponse)
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    token_dto = UsuarioService.autenticar_usuario(db, username=form_data.username, password=form_data.password)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token_dto.access_token}",
        httponly=True,
        samesite="lax",
        path="/"
    )
    return token_dto

@router.get("/me", response_model=UsuarioResponse)
def obtener_perfil_actual(current_user: Usuario = Depends(get_current_user)):
    return current_user