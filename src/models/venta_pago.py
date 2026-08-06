from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import Numeric, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.config.database import Base

if TYPE_CHECKING:
    from src.models.venta import Venta


class VentaPago(Base):
    """
    Representa la entidad de persistencia para el desglose de cobros/medios de pago de una venta.
    Mapea la tabla relacional 'venta_pagos' mediante SQLAlchemy ORM (Sintaxis 2.0+).
    Usa tipo Numeric para preservar precisión exactos en montos abonados.
    """
    __tablename__ = "venta_pagos"

    # Atributos de Identificación y Relación
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id"), nullable=False)

    # Canal o Medio de Pago ("Efectivo", "Transferencia", "Tarjeta", etc.)
    medio_pago: Mapped[str] = mapped_column(String(50), nullable=False)

    # Monto abonado con este medio específico
    monto: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # --- Relaciones Bidireccionales (ORM) ---

    # Relación bidireccional N-1 (Muchos registros de pago pertenecen a una venta cabecera)
    venta_cabecera: Mapped["Venta"] = relationship(
        "Venta",
        back_populates="pagos"
    )