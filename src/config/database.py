from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config.config import settings

# Esto va a crear un archivo llamado "almacen.db" en la raíz de tu proyecto
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# connect_args es necesario SOLO para SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# La dependencia para inyectar la BD en los endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()