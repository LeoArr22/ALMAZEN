from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# 1. Importamos la configuración global y la Base de los modelos
from src.config.config import settings
from src.config.database import Base

# Importamos todos los modelos para que Alembic detecte la estructura completa
import src.models

# Configuración de logs de Alembic
config = context.config

# Inyectamos la DATABASE_URL de tu archivo config.py / .env
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name:
    fileConfig(config.config_file_name)

# 2. Asignamos el Target Metadata para que detecte las tablas dinámicamente
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Modo offline: Genera SQL sin conectarse a la BD activa."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Modo online: Conecta a la BD e impacta los cambios."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = settings.DATABASE_URL
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()