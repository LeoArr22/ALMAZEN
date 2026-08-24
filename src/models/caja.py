from datetime import datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Numeric, ForeignKey
from src.config.database import Base 

# Prevención de importación circular para verificación de tipos en tiempo de análisis estático
if TYPE_CHECKING:
    from src.models.venta import Venta
    from src.models.usuario import Usuario

class Caja(Base):
    """
    Representa la entidad de persistencia para el control de turnos de caja.
    Mapea la tabla relacional 'cajas_turnos' mediante SQLAlchemy ORM (Sintaxis 2.0+).
    Incluye claves foráneas para auditoría de apertura y cierre por usuario.
    """
    __tablename__ = "cajas_turnos"

    # Atributos de Identificación y Temporalidad
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    fecha_apertura: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    fecha_cierre: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Atributos Financieros (Usa tipo Numeric para preservar precisión decimal exacta)
    monto_inicial: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    
    # nullable=True porque se calculan/ingresan al momento del cierre
    monto_final_estimado: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    monto_final_real: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Atributos de Estado de Ciclo de Vida
    estado: Mapped[str] = mapped_column(String(20), default="ABIERTA")  # "ABIERTA" o "CERRADA"

    # --- CLAVES FORÁNEAS (NUEVAS): Auditoría de Usuarios ---
    # nullable=False asegura integridad a nivel BD para apertura
    usuario_apertura_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    
    # nullable=True porque se ingresa al momento del cierre
    usuario_cierre_id: Mapped[Optional[int]] = mapped_column(ForeignKey("usuarios.id"), nullable=True)

    # --- Relaciones Bidireccionales (ORM) ---
    
    # Relación inversa hacia Usuario: Quién abrió y quién cerró
    # foreign_keys explícitas necesarias al tener dos FKs apuntando a la misma tabla
    usuario_apertura: Mapped["Usuario"] = relationship(
        "Usuario", 
        foreign_keys=[usuario_apertura_id], 
        back_populates="cajas_aperturas"
    )
    
    usuario_cierre: Mapped[Optional["Usuario"]] = relationship(
        "Usuario", 
        foreign_keys=[usuario_cierre_id], 
        back_populates="cajas_cierres"
    )
    
    # Relación bidireccional 1-N (Una caja posee n ventas)
    ventas: Mapped[List["Venta"]] = relationship(
        "Venta", 
        back_populates="turno_caja"
    )
    
    # =========================================================================
    # 🌟 PROPIEDADES CALCULADAS DINÁMICAMENTE (Consumidas por CajaResponse)
    # =========================================================================

    @property
    def total_efectivo(self) -> Decimal:
        total = Decimal("0.00")
        for venta in self.ventas:
            if getattr(venta, "es_anulada", False):
                continue
            for pago in venta.pagos:
                if pago.medio_pago.upper() in ["EFECTIVO", "CASH"]:
                    total += pago.monto
        return total

    @property
    def total_transferencia(self) -> Decimal:
        total = Decimal("0.00")
        for venta in self.ventas:
            if getattr(venta, "es_anulada", False):
                continue
            for pago in venta.pagos:
                if pago.medio_pago.upper() in ["TRANSFERENCIA", "MP", "MERCADOPAGO"]:
                    total += pago.monto
        return total

    @property
    def total_tarjeta(self) -> Decimal:
        total = Decimal("0.00")
        for venta in self.ventas:
            if getattr(venta, "es_anulada", False):
                continue
            for pago in venta.pagos:
                if pago.medio_pago.upper() in ["TARJETA", "DEBITO", "CREDITO"]:
                    total += pago.monto
        return total

    @property
    def total_ventas(self) -> Decimal:
        return self.total_efectivo + self.total_transferencia + self.total_tarjeta