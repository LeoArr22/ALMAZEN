import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
from src.config.config import settings

def obtener_password_hash(password: str) -> str:
    """
    Recibe el string limpio de la contraseña (ej: 'admin123'),
    lo convierte a bytes, lo hashea de forma nativa con una sal
    y devuelve el string listo para guardar en la BD.
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    password_seguro_bytes = bcrypt.hashpw(password_bytes, salt)
    return password_seguro_bytes.decode('utf-8')

def verificar_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compara la contraseña en texto plano enviada por el usuario
    con el hash guardado en la base de datos de manera segura.
    """
    plain_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_bytes, hashed_bytes)

def crear_token_acceso(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Genera un token JWT firmado digitalmente con los datos provistos (payload).
    Asigna una fecha de expiración automática según la configuración del sistema.
    """
    to_encode = data.copy()
    
    # Si pasamos un tiempo de expiración personalizado lo usamos, sino usamos el del .env
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)    
    # El campo 'exp' le dice a JWT cuándo deja de ser válido el token
    to_encode.update({"exp": expire})
    
    # Firmamos el token con nuestra SECRET_KEY y el algoritmo elegido
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt