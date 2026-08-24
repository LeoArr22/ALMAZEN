from typing import Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.models.producto import Producto
from src.schemas.producto_schema import ProductoCreate, ProductoUpdate

class ProductoRepository:
    
    @staticmethod
    def crear(db: Session, producto_in: ProductoCreate) -> Producto:
        nuevo_producto = Producto(**producto_in.model_dump())
        db.add(nuevo_producto)
        db.flush()
        return nuevo_producto

    @staticmethod
    def obtener_por_codigo_barras(db: Session, codigo: str) -> Optional[Producto]:
        if not codigo:
            return None
        return db.scalars(
            select(Producto).where(Producto.codigo_barras == codigo.strip())
        ).first()
    
    @staticmethod
    def obtener_por_id(db: Session, producto_id: int) -> Optional[Producto]:
        return db.scalars(
            select(Producto).where(Producto.id == producto_id)
        ).first()

    @staticmethod
    def obtener_todos(db: Session, skip: int = 0, limit: int = 500) -> list[Producto]:
        return list(
            db.scalars(
                select(Producto).offset(skip).limit(limit)
            ).all()
        )

    @staticmethod
    def obtener_por_nombre(db: Session, nombre: str) -> list[Producto]:
        return list(
            db.scalars(
                select(Producto).where(Producto.nombre.ilike(f"%{nombre}%"))
            ).all()
        )

    @staticmethod
    def obtener_por_categoria(db: Session, categoria: str) -> list[Producto]:
        return list(
            db.scalars(
                select(Producto).where(Producto.categoria.ilike(f"%{categoria}%"))
            ).all()
        )

    @staticmethod
    def obtener_con_bajo_stock(db: Session, limite_stock: int = 5) -> list[Producto]:
        return list(
            db.scalars(
                select(Producto).where(Producto.stock <= limite_stock)
            ).all()
        )

    @staticmethod
    def editar(db: Session, db_producto: Producto, producto_in: ProductoUpdate) -> Producto:
        datos_actualizar = producto_in.model_dump(exclude_unset=True)
        for campo, valor in datos_actualizar.items():
            if hasattr(db_producto, campo):
                setattr(db_producto, campo, valor)
        db.flush()
        return db_producto

    @staticmethod
    def eliminar(db: Session, db_producto: Producto) -> None:
        db.delete(db_producto)

    @staticmethod
    def obtener_categorias_existentes(db: Session) -> list[str]:
        stmt = (
            select(Producto.categoria)
            .where(
                Producto.categoria.isnot(None), 
                Producto.categoria != ""
            )
            .distinct()
        )
        return list(db.scalars(stmt).all())
    
    @staticmethod
    def obtener_por_id_para_update(db: Session, producto_id: int) -> Optional[Producto]:
        stmt = (
            select(Producto)
            .where(Producto.id == producto_id)
            .with_for_update()
        )
        return db.scalars(stmt).first()
    
    @staticmethod
    def descontar_stock(db: Session, producto: Producto, cantidad: Decimal) -> Producto:
        producto.stock -= cantidad
        return producto