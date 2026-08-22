from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config.config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Configuración condicional de kwargs para el engine
engine_kwargs = {}

# check_same_thread es un parámetro exclusivo de SQLite
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    **engine_kwargs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Si el endpoint termina con éxito, confirma todos los cambios
    except Exception:
        db.rollback() # Si hubo un HTTPException o error no controlado, revierte todo
        raise
    finally:
        db.close()