import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

class Settings:
    # 1. Base de datos
    _db_url: str = os.getenv("DATABASE_URL", "sqlite:///./almacen.db")
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    DATABASE_URL: str = _db_url
    
    # 2. Seguridad
    _secret_key = os.getenv("SECRET_KEY")
    if not _secret_key:
        raise ValueError("CRÍTICO: No se ha configurado la variable de entorno SECRET_KEY.")

    SECRET_KEY: str = _secret_key

    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

settings = Settings()