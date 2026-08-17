from sqlalchemy.orm import Session
from typing import List
from fastapi import HTTPException, status
from src.repositories.usuario_repository import UsuarioRepository
from src.schemas.usuario_schema import UsuarioCreate, UsuarioUpdate, TokenResponse
from src.config.security import obtener_password_hash, verificar_password, crear_token_acceso

class UsuarioService:

    @staticmethod
    def registrar_usuario(db: Session, usuario_in: UsuarioCreate):
        usuario_existente = UsuarioRepository.obtener_por_username(db, usuario_in.username)
        if usuario_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El nombre de usuario '{usuario_in.username}' ya está registrado."
            )
        
        try:
            password_hasheado = obtener_password_hash(usuario_in.password)
            nuevo_usuario = UsuarioRepository.crear(db, usuario_in, password_hasheado)
            db.commit()
            db.refresh(nuevo_usuario)
            return nuevo_usuario
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def autenticar_usuario(db: Session, username: str, password: str) -> TokenResponse:
        usuario = UsuarioRepository.obtener_por_username(db, username=username)
        
        if not usuario or not verificar_password(password, usuario.password_hashed):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nombre de usuario o contraseña incorrectos.",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        if not usuario.activo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El usuario se encuentra desactivado."
            )

        token_data = {"sub": usuario.username}
        access_token = crear_token_acceso(data=token_data)
        return TokenResponse(access_token=access_token, token_type="bearer")

    @staticmethod
    def listar_usuarios(db: Session):
        return UsuarioRepository.obtener_todos(db)

    @staticmethod
    def actualizar_usuario(db: Session, usuario_id: int, usuario_in: UsuarioUpdate):
        usuario_db = UsuarioRepository.obtener_por_id(db, usuario_id)
        if not usuario_db:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")

        datos_actualizar = usuario_in.model_dump(exclude_unset=True)

        # 🛑 RESTRICCIÓN ADMIN: No se puede cambiar el nombre del usuario 'admin'
        if usuario_db.username == "admin" and "username" in datos_actualizar and datos_actualizar["username"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No está permitido modificar el nombre del usuario administrador principal ('admin')."
            )

        # Si viene actualización de username, verificar duplicados
        if "username" in datos_actualizar and datos_actualizar["username"] != usuario_db.username:
            existente = UsuarioRepository.obtener_por_username(db, datos_actualizar["username"])
            if existente:
                raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso.")

        # Si viene contraseña, se hashea antes de guardar
        if "password" in datos_actualizar:
            pwd = datos_actualizar.pop("password")
            if pwd and len(pwd.strip()) >= 6:
                datos_actualizar["password_hashed"] = obtener_password_hash(pwd)

        try:
            usuario = UsuarioRepository.actualizar(db, usuario_db, datos_actualizar)
            db.commit()
            db.refresh(usuario)
            return usuario
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def alternar_estado_usuario(db: Session, usuario_id: int):
        usuario_db = UsuarioRepository.obtener_por_id(db, usuario_id)
        if not usuario_db:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")

        # 🛑 RESTRICCIÓN ADMIN: No se puede deshabilitar al usuario 'admin'
        if usuario_db.username == "admin" and usuario_db.activo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede deshabilitar al usuario administrador principal ('admin')."
            )

        try:
            usuario = UsuarioRepository.actualizar(db, usuario_db, {"activo": not usuario_db.activo})
            db.commit()
            db.refresh(usuario)
            return usuario
        except Exception as e:
            db.rollback()
            raise e