from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.repositories.promocion_repository import PromocionRepository
from src.repositories.producto_repository import ProductoRepository
from src.schemas.promocion_schema import PromocionCreate, PromocionUpdate
from src.models.promocion import Promocion

class PromocionService:

    @staticmethod
    def crear_promocion(db: Session, promo_in: PromocionCreate) -> Promocion:
        tipo_upper = promo_in.tipo.upper()
        tipos_validos = ["CANTIDAD", "MULTIPLO", "CANTIDAD_MINIMA", "COMBO"]

        if tipo_upper not in tipos_validos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de promoción inválido. Debe ser uno de: {', '.join(tipos_validos)}"
            )

        # 1. Validar existencia de cada producto
        for item in promo_in.productos:
            producto = ProductoRepository.obtener_por_id(db, item.producto_id)
            if not producto:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"El producto con ID {item.producto_id} no existe."
                )

        # 2. Regla: Promociones individuales (1 solo producto)
        if tipo_upper in ["CANTIDAD", "MULTIPLO", "CANTIDAD_MINIMA"] and len(promo_in.productos) != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Las promociones de tipo {tipo_upper} deben asociarse a exactamente 1 producto."
            )

        # 3. Regla: Promociones de tipo COMBO (al menos 2 productos)
        if tipo_upper == "COMBO" and len(promo_in.productos) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un combo debe incluir al menos 2 productos distintos."
            )

        # Normalizamos tipo a mayúsculas
        promo_in.tipo = tipo_upper

        return PromocionRepository.crear(db, promo_in)

    @staticmethod
    def obtener_promocion(db: Session, promocion_id: int) -> Promocion:
        promo = PromocionRepository.obtener_por_id(db, promocion_id)
        if not promo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Promoción con ID {promocion_id} no encontrada."
            )
        return promo

    @staticmethod
    def listar_promociones(db: Session, solo_activas: bool = True) -> list[Promocion]:
        return PromocionRepository.obtener_todas(db, solo_activas)

    @staticmethod
    def modificar_promocion(db: Session, promocion_id: int, promo_in: PromocionUpdate) -> Promocion:
        db_promo = PromocionService.obtener_promocion(db, promocion_id)
        if promo_in.tipo:
            promo_in.tipo = promo_in.tipo.upper()
        return PromocionRepository.editar(db, db_promo, promo_in)

    @staticmethod
    def borrar_promocion(db: Session, promocion_id: int) -> dict:
        db_promo = PromocionService.obtener_promocion(db, promocion_id)
        PromocionRepository.eliminar(db, db_promo)
        return {"message": f"Promoción '{db_promo.nombre}' eliminada correctamente."}