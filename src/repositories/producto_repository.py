from typing import Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, select
from src.models.producto import Producto
from src.schemas.producto_schema import ProductoCreate, ProductoUpdate

class ProductoRepository:
    
    @staticmethod
    def crear(db: Session, producto_in: ProductoCreate) -> Producto:
        # Transformamos el DTO de Pydantic a un Modelo de SQLAlchemy
        nuevo_producto = Producto(**producto_in.model_dump())
        db.add(nuevo_producto)
        db.commit()
        db.refresh(nuevo_producto)
        return nuevo_producto

    @staticmethod
    def obtener_por_codigo_barras(db: Session, codigo: str) -> Optional[Producto]:
        """
        Busca un producto en la base de datos usando su código de barras único.
        Útil para la integración futura con el lector de códigos de barra físico.
        """
        if not codigo:
            return None

        # select(Producto) arma la consulta.
        # db.scalars(...) ejecuta y extrae los objetos limpios de Python.
        # .first() agarra el primero que encuentra (o None si no hay coincidencia).
        return db.scalars(select(Producto).filter(Producto.codigo_barras == codigo.strip())).first()
    
    @staticmethod
    def obtener_por_id(db: Session, producto_id: int) -> Producto:
        return db.query(Producto).filter(Producto.id == producto_id).first()

    @staticmethod
    def obtener_todos(db: Session, skip: int = 0, limit: int = 500) -> list[Producto]:
        return db.query(Producto).offset(skip).limit(limit).all()

    @staticmethod
    def obtener_por_nombre(db: Session, nombre: str) -> list[Producto]:
        # Usamos ilike para que no importe si busca en mayúsculas o minúsculas
        return db.query(Producto).filter(Producto.nombre.ilike(f"%{nombre}%")).all()

    @staticmethod
    def obtener_por_categoria(db: Session, categoria: str) -> list[Producto]:
        return db.query(Producto).filter(Producto.categoria.ilike(f"%{categoria}%")).all()

    @staticmethod
    def obtener_con_bajo_stock(db: Session, limite_stock: int = 5) -> list[Producto]:
        # Trae los productos cuyo stock sea menor o igual al límite enviado
        return db.query(Producto).filter(Producto.stock <= limite_stock).all()

    @staticmethod
    def editar(db: Session, db_producto: Producto, producto_in: ProductoUpdate) -> Producto:
        # Obtenemos solo los campos que el usuario envió para modificar
        datos_actualizar = producto_in.model_dump(exclude_unset=True)
        
        for campo, valor in datos_actualizar.items():
            if hasattr(db_producto, campo):
                setattr(db_producto, campo, valor)
            
        db.commit()
        db.refresh(db_producto)
        return db_producto

    @staticmethod
    def eliminar(db: Session, db_producto: Producto) -> None:
        db.delete(db_producto)
        db.commit()

    @staticmethod
    def obtener_categorias_existentes(db: Session) -> list[str]:
        # El truco que hablamos para listar las categorías únicas cargadas en el campo de texto
        resultado = db.query(Producto.categoria).distinct().all()
        # Como devuelve una lista de tuplas [("Almacén",), ("Bebidas",)], lo limpiamos a una lista de strings
        return [r[0] for r in resultado]
    
    @staticmethod
    def obtener_por_id_para_update(db: Session, producto_id: int) -> Producto:
        """Busca un producto por ID aplicando un bloqueo pesimista (FOR UPDATE) 
        para evitar que dos cajas vendan sin stock en simultáneo."""
        return db.query(Producto).filter(Producto.id == producto_id).with_for_update().first()