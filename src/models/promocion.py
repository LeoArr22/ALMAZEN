from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.config.database import Base

if TYPE_CHECKING:
    from src.models.producto import Producto

class PromocionProducto(Base):
    __tablename__ = "promocion_productos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    promocion_id: Mapped[int] = mapped_column(ForeignKey("promociones.id", ondelete="CASCADE"))
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="CASCADE"))
    
    # Cantidad requerida de este producto para activar la promo (ej: 3 para 3kg, o 1 para Fernet)
    cantidad_requerida: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=Decimal("1.000"))

    # Relaciones
    promocion: Mapped["Promocion"] = relationship("Promocion", back_populates="productos")
    producto: Mapped["Producto"] = relationship("Producto")


class Promocion(Base):
    __tablename__ = "promociones"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), index=True) # ej: "3kg Balanceado x $5000" o "Combo Fernet + Coca"
    descripcion: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    
    # "CANTIDAD" (para volumen de 1 solo producto) o "COMBO" (para varios productos distintos)
    tipo: Mapped[str] = mapped_column(String(20), default="CANTIDAD") 
    
    precio_promocional: Mapped[Decimal] = mapped_column(Numeric(10, 2)) # Precio final cerrado de la oferta
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    # Lista de productos que forman parte de la promoción
    productos: Mapped[List["PromocionProducto"]] = relationship(
        "PromocionProducto", back_populates="promocion", cascade="all, delete-orphan"
    )