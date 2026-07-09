import os
from pathlib import Path
from dotenv import load_dotenv

# 1. Localizamos la raíz del proyecto dinámicamente desde este archivo
# src/config/config.py -> src/config -> src -> raíz (donde está el .env)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

# 2. Cargamos las variables de entorno del archivo .env a la memoria del sistema
load_dotenv(dotenv_path=ENV_PATH)

class Settings:
    """
    Centraliza todas las variables de entorno de la aplicación.
    Provee valores por defecto si no se encuentran en el archivo .env.
    """
    # Configuración de Base de Datos
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./almacen.db")
    
    # Configuración de Seguridad y JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "clave_por_defecto_muy_debil")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

# Instancia única para importar en el resto del sistema (Patrón Singleton)
settings = Settings()