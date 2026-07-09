from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.schemas.venta_schema import VentaCreate
from src.models.venta import Venta
from src.models.caja import Caja 
from src.repositories.venta_repository import VentaRepository
from src.repositories.producto_repository import ProductoRepository 
from src.repositories.caja_repository import CajaRepository

class VentaService:

    @staticmethod
    def registrar_venta(db: Session, venta_in: VentaCreate, usuario_id: int) -> Venta:
        # 🔍 Validamos que exista una caja abierta antes de tocar nada
        caja_abierta = CajaRepository.obtener_activa(db)
        
        if not caja_abierta:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede registrar la venta: No existe ninguna caja abierta actualmente en el sistema."
            )

        # Inicializamos los acumuladores para la cabecera de la venta
        total_venta = 0.0
        ganancia_total_venta = 0.0
        
        # Estructura temporal para guardar lo que vamos validando antes de escribir en la BD
        productos_a_descontar = []

        try:
            # 1. PRIMER PASO: Validar todo el "carrito" bloqueando las filas desde el Repo
            for detalle in venta_in.detalles:
                producto = ProductoRepository.obtener_por_id_para_update(db, detalle.producto_id)
                
                if not producto:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"El producto con ID {detalle.producto_id} no existe."
                    )
                
                if producto.stock < detalle.cantidad:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Stock insuficiente para el producto '{producto.nombre}'. Disponible: {producto.stock}, Solicitado: {detalle.cantidad}"
                    )
                
                # Cálculo de subtotales basados en la información actual del producto
                subtotal_item = float(producto.precio) * detalle.cantidad
                costo_total_item = float(producto.costo) * detalle.cantidad
                
                total_venta += subtotal_item
                ganancia_total_venta += (subtotal_item - costo_total_item)
                
                # Almacenamos temporalmente los datos validados para su posterior persistencia
                productos_a_descontar.append({
                    "producto_obj": producto,
                    "cantidad": detalle.cantidad,
                    "precio_historico": float(producto.precio),
                    "costo_historico": float(producto.costo)
                })

            # 2. SEGUNDO PASO: Persistencia de la cabecera vinculando el usuario que opera
            db_venta = VentaRepository.crear_cabecera(
                db=db, 
                total=total_venta, 
                ganancia_total=ganancia_total_venta, 
                caja_id=caja_abierta.id,
                usuario_id=usuario_id
            )

            # 3. TERCER PASO: Registrar cada renglón de detalle y actualizar existencias de inventario
            for item in productos_a_descontar:
                VentaRepository.crear_detalle(
                    db=db,
                    venta_id=db_venta.id,
                    producto_id=item["producto_obj"].id,
                    cantidad=item["cantidad"],
                    precio_historico=item["precio_historico"],
                    costo_historico=item["costo_historico"]
                )
                
                # Reducción de existencias en memoria del ORM
                item["producto_obj"].stock -= item["cantidad"]

            # Confirmación atómica de la transacción completa
            db.commit()
            
            return VentaService.obtener_venta(db, db_venta.id)

        except Exception as e:
            # Reversión de cualquier cambio ante fallas para preservar la integridad de datos
            db.rollback()
            raise e    
        
    @staticmethod
    def obtener_venta(db: Session, venta_id: int) -> Venta:
        # Llama al repositorio que ya viene con el joinedload incorporado
        db_venta = VentaRepository.obtener_por_id(db, venta_id)
        if not db_venta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"La operación de venta N° {venta_id} no existe en el sistema."
            )
        return db_venta
    
    @staticmethod
    def listar_ventas_por_vendedor(db: Session, usuario_id: int, skip: int = 0, limit: int = 100) -> list[Venta]:
        """
        Recupera el historial de operaciones de venta filtrado por el identificador del vendedor.
        Pasa la solicitud directamente al repositorio aplicando paginación estándar.
        """
        return VentaRepository.obtener_por_vendedor(db, usuario_id, skip, limit)

    # En src/services/venta_service.py

    @staticmethod
    def listar_ventas(
        db: Session, 
        skip: int = 0, 
        limit: int = 100, 
        caja_id: Optional[int] = None, 
        fecha: Optional[str] = None
    ) -> list[Venta]:
        """Recupera el historial delegando los filtros al repositorio."""
        return VentaRepository.obtener_todas(db, skip, limit, caja_id, fecha)

    @staticmethod
    def cancelar_venta(db: Session, venta_id: int) -> None:
        """
        Cancela una venta: devuelve el stock a los productos y elimina el registro.
        """
        # El método ya valida de forma nativa si no existe la venta lanzando un 404 prolijo
        db_venta = VentaService.obtener_venta(db, venta_id)
        
        # Devolvemos la mercadería al stock antes de borrar los renglones
        for detalle in db_venta.detalles:
            # Validamos que el producto_id exista (que no sea None) antes de llamar al repositorio
            if detalle.producto_id is not None:
                producto = ProductoRepository.obtener_por_id(db, detalle.producto_id)
                if producto:
                    producto.stock += detalle.cantidad
                
        VentaRepository.eliminar(db, db_venta)
        db.commit()  # Aseguramos el impacto definitivo del borrado y la devolución del stock