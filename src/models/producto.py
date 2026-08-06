from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Numeric, Boolean
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
    
    # 🌟 AHORA PERMITE DECIMALES (ej: 12.500 kg)
    stock: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=Decimal("0.000"))
    
    # 🌟 NUEVOS CAMPOS FRACCIONABLES
    es_fraccionable: Mapped[bool] = mapped_column(Boolean, default=False)
    unidad_medida: Mapped[str] = mapped_column(String(20), default="UNIDAD")  # "UNIDAD", "KG", "LITROS"
    
    costo: Mapped[Decimal] = mapped_column(Numeric(10, 2))   
    precio: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    
    codigo_barras: Mapped[Optional[str]] = mapped_column(
        String(50), unique=True, index=True, nullable=True, default=None
    )  

    detalles_venta: Mapped[List["VentaDetalle"]] = relationship("VentaDetalle", back_populates="producto")