import jwt
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.config.config import settings
from src.repositories.usuario_repository import UsuarioRepository
from src.models.usuario import Usuario

# auto_error=False es la clave: evita que FastAPI tire un 401 automático si no viene el header,
# permitiéndonos buscar el token manualmente en las cookies si el usuario entra por navegador.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/usuarios/login", auto_error=False)

async def get_current_user(
    request: Request,  # 🌟 Recibimos la Request para poder leer las cookies del navegador
    token: Optional[str] = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> Usuario:
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales de acceso.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_final: Optional[str] = None

    # 1. Intentamos buscar el token en las cookies del navegador (Para las vistas HTML)
    if request.cookies is not None:
        token_cookie = request.cookies.get("access_token")
        if token_cookie:
            token_final = token_cookie

    # 2. Si la cookie tiene el formato "Bearer <token>", le limpiamos el prefijo
    if token_final and token_final.startswith("Bearer "):
        partes = token_final.split(" ")
        if len(partes) > 1:
            token_final = partes[1]
        
    # 3. Si no había token en la cookie, usamos el que mandó el Header (Para Swagger / API)
    if not token_final:
        token_final = token

    # 4. Si después de revisar ambos lados seguimos sin token, lanzamos el error
    if not token_final:
        raise credentials_exception

    try:
        payload = jwt.decode(token_final, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if not username:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    usuario = UsuarioRepository.obtener_por_username(db, username=username)
    if usuario is None:
        raise credentials_exception
        
    return usuario