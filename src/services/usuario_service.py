from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.repositories.usuario_repository import UsuarioRepository
from src.schemas.usuario_schema import UsuarioCreate, TokenResponse  # Sácamos UsuarioLogin que ya no se usa acá
from src.config.security import obtener_password_hash, verificar_password, crear_token_acceso

class UsuarioService:

    @staticmethod
    def registrar_usuario(db: Session, usuario_in: UsuarioCreate):
        """
        Registra un nuevo usuario en el sistema aplicando el hashing 
        de la contraseña antes de persistir los datos.
        """
        # 1. Validamos que el nombre de usuario no esté duplicado
        usuario_existente = UsuarioRepository.obtener_por_username(db, usuario_in.username)
        if usuario_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El nombre de usuario '{usuario_in.username}' ya está registrado en el sistema."
            )
        
        try:
            # 2. Transformamos la contraseña en un hash seguro irreversible
            password_hasheado = obtener_password_hash(usuario_in.password)
            
            # 3. Delegamos la inserción pasiva al repositorio
            nuevo_usuario = UsuarioRepository.crear(db, usuario_in, password_hasheado)
            
            # 4. El servicio confirma de forma atómica la transacción en disco
            db.commit()
            db.refresh(nuevo_usuario)
            return nuevo_usuario
            
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def autenticar_usuario(db: Session, username: str, password: str) -> TokenResponse:
        """
        Valida las credenciales del usuario (enviadas como parámetros sueltos)
        y retorna un token JWT válido si la autenticación resulta exitosa.
        """
        # 1. Buscamos al usuario por su nombre único (ahora usando el string directo)
        usuario = UsuarioRepository.obtener_por_username(db, username=username)
        
        # 2. Si no existe o la contraseña no matchea con el hash, lanzamos 401 (Unauthorized)
        # Usamos el método verificar_password de tu seguridad corregida con bcrypt nativo
        if not usuario or not verificar_password(password, usuario.password_hashed):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nombre de usuario o contraseña incorrectos.",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # 3. Preparamos el 'payload' (los datos internos del token)
        token_data = {"sub": usuario.username}
        
        # 4. Creamos el token firmado digitalmente
        access_token = crear_token_acceso(data=token_data)
        
        # 5. Devolvemos el DTO mapeado con Pydantic (¡Pydantic sigue vivo aca para estructurar la salida!)
        return TokenResponse(access_token=access_token, token_type="bearer")