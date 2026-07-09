from decimal import Decimal
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.config.database import Base

if TYPE_CHECKING:
    from src.models.caja import Caja
    from src.models.producto import Producto
    from src.models.usuario import Usuario

class Venta(Base):
    """
    Representa la entidad de persistencia para la cabecera de las operaciones de venta.
    Mapea la tabla relacional 'ventas' mediante SQLAlchemy ORM (Sintaxis 2.0+).
    Incluye clave foránea para auditoría del vendedor que realizó la operación.
    """
    __tablename__ = "ventas"

    # Atributos de Identificación y Temporalidad
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    fecha_venta: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # Atributos Financieros (Usa tipo Numeric para preservar precisión exacta)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    ganancia_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # --- CLAVES FORÁNEAS (NUEVAS Y EXISTENTES) ---
    caja_id: Mapped[int] = mapped_column(ForeignKey("cajas_turnos.id"), nullable=False)
    
    # nullable=False asegura integridad a nivel BD para la auditoría
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False) # Quién hizo la venta

    # --- Relaciones Bidireccionales (ORM) ---
    
    # Relación bidireccional N-1 (Muchas ventas pertenecen a una caja)
    turno_caja: Mapped["Caja"] = relationship(
        "Caja", 
        back_populates="ventas"
    )
    
    # Relación bidireccional N-1 (Muchas ventas pertenecen a un vendedor/usuario)
    vendedor: Mapped["Usuario"] = relationship(
        "Usuario", 
        back_populates="ventas"
    )
    
    # Relación bidireccional 1-N (Una venta madre posee n renglones/detalles hijos)
    # cascade asegura borrado en cascada atómico a nivel ORM
    detalles: Mapped[List["VentaDetalle"]] = relationship(
        "VentaDetalle", 
        back_populates="venta_cabecera", 
        cascade="all, delete-orphan"
    )


class VentaDetalle(Base):
    """
    Representa la entidad de persistencia para los renglones (detalles) individuales de una venta.
    Mapea la tabla relacional 'ventas_detalles' mediante SQLAlchemy ORM (Sintaxis 2.0+).
    Usa tipos Numeric para congelar costos y precios históricos exactos.
    """
    __tablename__ = "ventas_detalles"

    # Atributos de Identificación y Relación
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id"), nullable=False)
    
    # nullable=True por si se borra el producto pero queremos el historial íntegro
    producto_id: Mapped[Optional[int]] = mapped_column(ForeignKey("productos.id"), nullable=True) 
    
    # Atributo de Cantidad (entero)
    cantidad: Mapped[int] = mapped_column(nullable=False)
    
    # --- Atributos Financieros (Usa tipo Numeric para precisión decimal exacta) ---
    # Precios congelados al momento exacto de la venta (no cambian si cambia el producto luego)
    precio_historico: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    costo_historico: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    ganancia_item: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # --- Relaciones Bidireccionales (ORM) ---
    
    # Relación bidireccional N-1 (Muchos renglones pertenecen a una venta cabecera)
    venta_cabecera: Mapped["Venta"] = relationship(
        "Venta", 
        back_populates="detalles"
    )
    
    # Relación bidireccional N-1 (Muchos renglones apuntan a un producto para consulta rápida de nombre)
    producto: Mapped[Optional["Producto"]] = relationship("Producto")