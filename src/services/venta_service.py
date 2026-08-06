from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.schemas.venta_schema import VentaCreate
from src.models.venta import Venta
from src.repositories.venta_repository import VentaRepository
from src.repositories.producto_repository import ProductoRepository 
from src.repositories.caja_repository import CajaRepository
from src.repositories.usuario_repository import UsuarioRepository

class VentaService:

    @staticmethod
    def registrar_venta(db: Session, venta_in: VentaCreate, usuario_id: int) -> Venta:
        # 1. Verificar si la venta contiene un consumo interno
        es_consumo_interno = any(
            pago.medio_pago.upper() == "CONSUMO_INTERNO" for pago in venta_in.pagos
        )

        # 2. Si es consumo interno, validar permisos usando el repositorio de usuarios
        if es_consumo_interno:
            usuario_actual = UsuarioRepository.obtener_por_id(db, usuario_id)
            if not usuario_actual or str(usuario_actual.role).lower() != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo los usuarios con rol ADMINISTRADOR pueden registrar consumos internos."
                )

        # 3. Buscar turno de caja abierto asignado al usuario
        caja_abierta = CajaRepository.obtener_activa_por_usuario(db, usuario_id)
        
        if not caja_abierta:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No podés registrar la venta: No tenés un turno de caja abierto a tu nombre."
            )

        total_venta = Decimal("0.00")
        ganancia_total_venta = Decimal("0.00")
        productos_a_descontar = []

        try:
            # 4. Validar existencia y stock de productos
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
                        detail=f"Stock insuficiente para '{producto.nombre}'. Disponible: {producto.stock}, Solicitado: {detalle.cantidad}"
                    )

                subtotal = producto.precio * detalle.cantidad
                costo_total = producto.costo * detalle.cantidad
                ganancia_item = subtotal - costo_total

                total_venta += subtotal
                ganancia_total_venta += ganancia_item

                productos_a_descontar.append({
                    "producto_obj": producto,
                    "cantidad": detalle.cantidad,
                    "precio_historico": producto.precio,
                    "costo_historico": producto.costo
                })

            # 5. Persistir cabecera de venta
            db_venta = VentaRepository.crear_cabecera(
                db=db,
                total=total_venta if not es_consumo_interno else Decimal("0.00"),
                ganancia_total=Decimal("0.00") if es_consumo_interno else ganancia_total_venta,
                caja_id=caja_abierta.id,
                usuario_id=usuario_id
            )

            # 6. Insertar renglones de detalle y actualizar stock
            for item in productos_a_descontar:
                VentaRepository.crear_detalle(
                    db=db,
                    venta_id=db_venta.id,
                    producto_id=item["producto_obj"].id,
                    cantidad=item["cantidad"],
                    precio_historico=item["precio_historico"],
                    costo_historico=item["costo_historico"]
                )
                ProductoRepository.descontar_stock(
                    db=db,
                    producto=item["producto_obj"],
                    cantidad=item["cantidad"]
                )

            # 7. Registrar desgloses de pago
            for pago in venta_in.pagos:
                VentaRepository.crear_pago(
                    db=db,
                    venta_id=db_venta.id,
                    medio_pago=pago.medio_pago,
                    monto=pago.monto
                )

            db.commit()
            db.refresh(db_venta)
            return db_venta

        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error interno al procesar la operación: {str(e)}"
            )

    @staticmethod
    def obtener_venta(db: Session, venta_id: int) -> Venta:
        db_venta = VentaRepository.obtener_por_id(db, venta_id)
        if not db_venta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"La operación de venta N° {venta_id} no existe en el sistema."
            )
        return db_venta

    @staticmethod
    def listar_ventas_por_vendedor(db: Session, usuario_id: int, skip: int = 0, limit: int = 100) -> list[Venta]:
        return VentaRepository.obtener_por_vendedor(db, usuario_id, skip, limit)

    @staticmethod
    def listar_ventas(
        db: Session, 
        skip: int = 0, 
        limit: int = 100, 
        caja_id: Optional[int] = None, 
        fecha: Optional[str] = None
    ) -> list[Venta]:
        return VentaRepository.obtener_todas(db, skip, limit, caja_id, fecha)

    @staticmethod
    def cancelar_venta(db: Session, venta_id: int) -> None:
        db_venta = VentaService.obtener_venta(db, venta_id)
        
        try:
            for detalle in db_venta.detalles:
                if detalle.producto_id:
                    producto = ProductoRepository.obtener_por_id_para_update(db, detalle.producto_id)
                    if producto:
                        producto.stock += Decimal(str(detalle.cantidad))

            VentaRepository.eliminar(db, db_venta)
            db.commit()
        except Exception as e:
            db.rollback()
            raise e