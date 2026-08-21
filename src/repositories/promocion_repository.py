from typing import Optional
from sqlalchemy.orm import Session, joinedload
from src.models.promocion import Promocion, PromocionProducto
from src.schemas.promocion_schema import PromocionCreate, PromocionUpdate

class PromocionRepository:

    @staticmethod
    def obtener_por_id(db: Session, promocion_id: int) -> Optional[Promocion]:
        return (
            db.query(Promocion)
            .options(joinedload(Promocion.productos))
            .filter(Promocion.id == promocion_id)
            .first()
        )

    @staticmethod
    def obtener_todas(db: Session, solo_activas: bool = True) -> list[Promocion]:
        query = db.query(Promocion).options(joinedload(Promocion.productos))
        if solo_activas:
            query = query.filter(Promocion.activo == True)
        return query.all()

    @staticmethod
    def crear(db: Session, promo_in: PromocionCreate) -> Promocion:
        nueva_promo = Promocion(
            nombre=promo_in.nombre,
            descripcion=promo_in.descripcion,
            tipo=promo_in.tipo.upper(),
            precio_promocional=promo_in.precio_promocional,
            activo=promo_in.activo
        )
        db.add(nueva_promo)
        db.flush()  # Genera el ID para asociar los detalles

        for item in promo_in.productos:
            detalle = PromocionProducto(
                promocion_id=nueva_promo.id,
                producto_id=item.producto_id,
                cantidad_requerida=item.cantidad_requerida
            )
            db.add(detalle)

        db.commit()
        db.refresh(nueva_promo)
        return nueva_promo

    @staticmethod
    def editar(db: Session, db_promo: Promocion, promo_in: PromocionUpdate) -> Promocion:
        datos_actualizar = promo_in.model_dump(exclude_unset=True)
        for campo, valor in datos_actualizar.items():
            if hasattr(db_promo, campo):
                setattr(db_promo, campo, valor)

        db.commit()
        db.refresh(db_promo)
        return db_promo

    @staticmethod
    def eliminar(db: Session, db_promo: Promocion) -> None:
        db.delete(db_promo)
        db.commit()