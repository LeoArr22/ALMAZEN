from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.config.database import Base

if TYPE_CHECKING:
    from src.models.venta import VentaDetalle

class Producto(Base):
    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), index=True)
    descripcion: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    categoria: Mapped[str] = mapped_column(String(50), index=True)
    stock: Mapped[int] = mapped_column(default=0)
    
    # Mapped[Decimal] le dice al linter que esto se opera como un float/Decimal en Python
    costo: Mapped[Decimal] = mapped_column(Numeric(10, 2))   
    precio: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    
    codigo_barras: Mapped[Optional[str]] = mapped_column(
        String(50), 
        unique=True, 
        index=True, 
        nullable=True, 
        default=None
    )  

    # Relación inversa con la tabla intermedia (Tipado explícito de la lista)
    detalles: Mapped[List["VentaDetalle"]] = relationship(back_populates="producto")