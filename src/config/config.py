import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

class Settings:
    """
    Centraliza todas las variables de entorno de la aplicación.
    Provee valores por defecto si no se encuentran en el archivo .env.
    """
    # 1. Leemos la variable de entorno
    _db_url: str = os.getenv("DATABASE_URL", "sqlite:///./almacen.db")

    # 2. Corregimos el dialecto para SQLAlchemy si viene como postgres://
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)

    DATABASE_URL: str = _db_url
    
    # Configuración de Seguridad y JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "clave_por_defecto_muy_debil")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

settings = Settings()