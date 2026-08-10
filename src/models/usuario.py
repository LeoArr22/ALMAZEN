from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean
from src.config.database import Base 


# Prevención de importación circular para verificación de tipos en tiempo de análisis estático
# No tocar para que Mypy/Pyright sigan funcionando impecables
if TYPE_CHECKING:
    from src.models.venta import Venta
    from src.models.caja import Caja

# ==========================================
# 1. MODELO DE USUARIO (NUEVO)
# ==========================================
class Usuario(Base):
    """
    Representa la entidad de persistencia para los usuarios del sistema.
    Mapea la tabla relacional 'usuarios' mediante SQLAlchemy ORM (Sintaxis 2.0+).
    Soporta roles de 'admin' y 'vendedor'.
    """
    __tablename__ = "usuarios"

    # Atributos de Identificación y Autenticación
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # nullable=False asegura integridad a nivel BD
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hashed: Mapped[str] = mapped_column(String, nullable=False)  # Clave encriptada (no texto plano)
    
    # Atributo de Rol para control de acceso (ej: "admin" o "vendedor")
    role: Mapped[str] = mapped_column(String(20), nullable=False) 
    
    # Atributo de Estado para habilitar/deshabilitar usuarios sin borrarlos
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- Relaciones Bidireccionales 1-N (Un usuario posee n cajas y n ventas) ---
    
    # Relaciones hacia Caja: Un usuario puede abrir/cerrar muchas cajas
    # Se usan foreign_keys explícitas para distinguir qué relación es cuál
    cajas_aperturas: Mapped[List["Caja"]] = relationship(
        "Caja", 
        foreign_keys="Caja.usuario_apertura_id", 
        back_populates="usuario_apertura"
    )
    
    cajas_cierres: Mapped[List["Caja"]] = relationship(
        "Caja", 
        foreign_keys="Caja.usuario_cierre_id", 
        back_populates="usuario_cierre"
    )
    
    # Relación hacia Venta: Un usuario puede realizar muchas ventas
    ventas: Mapped[List["Venta"]] = relationship(
        "Venta", 
        back_populates="vendedor"
    )