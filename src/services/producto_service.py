from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from src.repositories.producto_repository import ProductoRepository
from src.schemas.producto_schema import ProductoCreate, ProductoUpdate
from src.models.producto import Producto

class ProductoService:

    @staticmethod
    def crear_producto(db: Session, producto_in: ProductoCreate) -> Producto:
        # 1. Validación de negocio rápida: El precio de venta no puede ser menor al costo
        if producto_in.precio < producto_in.costo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El precio de venta no puede ser menor al costo del producto."
            )
        
        # 2. Delegamos la restricción de duplicados a la base de datos para evitar Race Conditions.
        # Capturamos la excepción de integridad (UNIQUE constraint) de SQLAlchemy de manera atómica.
        try:
            return ProductoRepository.crear(db, producto_in)
        except IntegrityError as e:
            err_msg = str(e.orig).lower()
            if "codigo_barras" in err_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El código de barras '{producto_in.codigo_barras}' ya se encuentra registrado."
                )
            elif "nombre" in err_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ya existe un producto registrado con el nombre '{producto_in.nombre}'."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El producto viola una restricción de unicidad en la base de datos."
                )

    @staticmethod
    def obtener_producto(db: Session, producto_id: int) -> Producto:
        producto = ProductoRepository.obtener_por_id(db, producto_id)
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {producto_id} no encontrado."
            )
        return producto

    @staticmethod
    def listar_productos(db: Session, skip: int = 0, limit: int = 500) -> list[Producto]:
        return ProductoRepository.obtener_todos(db, skip, limit)

    @staticmethod
    def buscar_por_nombre(db: Session, nombre: str) -> list[Producto]:
        return ProductoRepository.obtener_por_nombre(db, nombre)

    @staticmethod
    def obtener_por_codigo(db: Session, codigo_barras: str) -> Producto:
        """Busca un producto por su código de barras y lanza 404 si no lo encuentra."""
        producto = ProductoRepository.obtener_por_codigo_barras(db, codigo_barras)
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró ningún producto con el código de barras '{codigo_barras}'."
            )
        return producto

    @staticmethod
    def buscar_por_categoria(db: Session, categoria: str) -> list[Producto]:
        return ProductoRepository.obtener_por_categoria(db, categoria)

    @staticmethod
    def verificar_alerta_stock(db: Session, limite: int = 5) -> list[Producto]:
        return ProductoRepository.obtener_con_bajo_stock(db, limite)

    @staticmethod
    def modificar_producto(db: Session, producto_id: int, producto_in: ProductoUpdate) -> Producto:
        # 1. Verificamos que el producto exista antes de editar
        db_producto = ProductoService.obtener_producto(db, producto_id)
        
        # 2. Validar precios y costos
        nuevo_costo = producto_in.costo if producto_in.costo is not None else Decimal(str(db_producto.costo))
        nuevo_precio = producto_in.precio if producto_in.precio is not None else Decimal(str(db_producto.precio))
        
        if nuevo_precio < nuevo_costo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El precio de venta resultante no puede ser menor al costo."
            )

        # 3. Capturamos posibles duplicados por conflicto al actualizar
        try:
            return ProductoRepository.editar(db, db_producto, producto_in)
        except IntegrityError as e:
            err_msg = str(e.orig).lower()
            if "codigo_barras" in err_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El código de barras ingresado ya está asignado a otro producto."
                )
            elif "nombre" in err_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El nombre ingresado ya está siendo utilizado por otro producto."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Error de restricción al actualizar el producto."
                )

    @staticmethod
    def borrar_producto(db: Session, producto_id: int) -> dict:
        db_producto = ProductoService.obtener_producto(db, producto_id)
        ProductoRepository.eliminar(db, db_producto)
        return {"message": f"Producto '{db_producto.nombre}' eliminado correctamente."}

    @staticmethod
    def listar_categorias(db: Session) -> list[str]:
        return ProductoRepository.obtener_categorias_existentes(db)