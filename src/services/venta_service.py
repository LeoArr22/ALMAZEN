import copy
import itertools
from datetime import datetime, time
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.schemas.venta_schema import VentaCreate
from src.models.venta import Venta
from src.repositories.venta_repository import VentaRepository
from src.repositories.producto_repository import ProductoRepository 
from src.repositories.caja_repository import CajaRepository
from src.repositories.usuario_repository import UsuarioRepository
from src.repositories.promocion_repository import PromocionRepository

class VentaService:

    @classmethod
    def _aplicar_secuencia_promos(cls, items_base: List[Dict[str, Any]], orden_promos: list) -> tuple[Decimal, List[Dict[str, Any]]]:
        """
        Simula la aplicación de una secuencia específica de promociones sobre una copia limpia del carrito.
        Devuelve el TOTAL FINAL de la venta y la lista de ítems procesados guardando el nombre de la promo.
        """
        items = copy.deepcopy(items_base)

        for item in items:
            item["cant_disponible"] = item["cantidad"]
            item["subtotal"] = item["producto_obj"].precio * item["cantidad"]
            item["promocion_aplicada"] = None  # Inicializamos sin promo

        for promo in orden_promos:
            tipo_upper = (promo.tipo or "").upper()
            productos_promo = promo.productos
            if not productos_promo:
                continue

            # --- CASO 1: COMBOS ---
            if tipo_upper == "COMBO":
                max_combos_posibles = float("inf")
                total_lista_combo = Decimal("0.00")

                for p_promo in productos_promo:
                    req_cant = Decimal(str(p_promo.cantidad_requerida))
                    item = next((i for i in items if i["producto_obj"].id == p_promo.producto_id), None)
                    cant_disp = item["cant_disponible"] if item else Decimal("0")

                    combos_posibles = int(cant_disp // req_cant)
                    if combos_posibles < max_combos_posibles:
                        max_combos_posibles = combos_posibles

                    if item:
                        total_lista_combo += item["producto_obj"].precio * req_cant

                precio_promo_combo = Decimal(str(promo.precio_promocional))

                if max_combos_posibles > 0 and max_combos_posibles != float("inf") and precio_promo_combo < total_lista_combo:
                    factor_descuento = precio_promo_combo / total_lista_combo

                    for p_promo in productos_promo:
                        req_cant = Decimal(str(p_promo.cantidad_requerida))
                        item = next((i for i in items if i["producto_obj"].id == p_promo.producto_id), None)
                        if item:
                            unidades_usadas = Decimal(max_combos_posibles) * req_cant
                            descuento_unidad = item["producto_obj"].precio * (Decimal("1") - factor_descuento)
                            ahorro_item = unidades_usadas * descuento_unidad

                            item["subtotal"] -= ahorro_item
                            item["cant_disponible"] -= unidades_usadas
                            item["promocion_aplicada"] = promo.nombre  # 👈 Guardamos el nombre aquí

            # --- CASO 2: MÚLTIPLO / LOTE / CANTIDAD ---
            elif tipo_upper in ["MULTIPLO", "CANTIDAD"]:
                promo_prod = productos_promo[0]
                cant_bloque = Decimal(str(promo_prod.cantidad_requerida))
                item = next((i for i in items if i["producto_obj"].id == promo_prod.producto_id), None)

                if item and item["cant_disponible"] >= cant_bloque:
                    precio_unitario_promo = Decimal(str(promo.precio_promocional)) / cant_bloque

                    if precio_unitario_promo < item["producto_obj"].precio:
                        bloques = int(item["cant_disponible"] // cant_bloque)
                        unidades_en_promo = Decimal(bloques) * cant_bloque
                        descuento_unidad = item["producto_obj"].precio - precio_unitario_promo

                        item["subtotal"] -= (unidades_en_promo * descuento_unidad)
                        item["cant_disponible"] -= unidades_en_promo
                        item["promocion_aplicada"] = promo.nombre  # 👈 Guardamos el nombre aquí

            # --- CASO 3: CANTIDAD MÍNIMA / MAYORISTA ---
            elif tipo_upper in ["CANTIDAD_MINIMA"]:
                promo_prod = productos_promo[0]
                req_cant = Decimal(str(promo_prod.cantidad_requerida))
                item = next((i for i in items if i["producto_obj"].id == promo_prod.producto_id), None)

                if item and item["cant_disponible"] >= req_cant:
                    precio_unitario_promo = Decimal(str(promo.precio_promocional)) / req_cant

                    if precio_unitario_promo < item["producto_obj"].precio:
                        item["subtotal"] = item["cantidad"] * precio_unitario_promo
                        item["cant_disponible"] = Decimal("0")
                        item["promocion_aplicada"] = promo.nombre  # 👈 Guardamos el nombre aquí

        # Calculamos el total final del carrito resultante para esta simulación
        total_venta_simulada = sum((item["subtotal"] for item in items), Decimal("0.00"))
        return total_venta_simulada, items

    @classmethod
    def _calcular_subtotales_con_promociones(cls, db: Session, items_procesados: List[Dict[str, Any]]) -> None:
        promos_activas = PromocionRepository.obtener_todas(db, solo_activas=True)
        if not promos_activas:
            return

        # Map de consulta rápida: producto_id -> cantidad en el carrito
        cantidades_carrito = {item["producto_obj"].id: item["cantidad"] for item in items_procesados}

        # 1. Filtramos solo las promociones que REALMENTE aplican según la cantidad del carrito
        promos_aplicables = []
        for promo in promos_activas:
            if not promo.productos:
                continue

            tipo_upper = (promo.tipo or "").upper()

            if tipo_upper == "COMBO":
                # Un combo solo aplica si TODOS sus productos están en el carrito con la cantidad mínima
                cumple_combo = all(
                    cantidades_carrito.get(p.producto_id, Decimal("0")) >= Decimal(str(p.cantidad_requerida))
                    for p in promo.productos
                )
                if cumple_combo:
                    promos_aplicables.append(promo)
            else:
                # Para MULTIPLO, CANTIDAD, CANTIDAD_MINIMA: requiere que el producto esté y supere el requerimiento
                promo_prod = promo.productos[0]
                cant_disponible = cantidades_carrito.get(promo_prod.producto_id, Decimal("0"))
                cant_requerida = Decimal(str(promo_prod.cantidad_requerida))
                
                if cant_disponible >= cant_requerida:
                    promos_aplicables.append(promo)

        if not promos_aplicables:
            return

        # 2. Agrupamos promociones que comparten productos entre sí (conflictos)
        grupos_conflicto = []
        for promo in promos_aplicables:
            prods_p = {p.producto_id for p in promo.productos}
            agregado = False
            for grupo in grupos_conflicto:
                if any(prods_p.intersection({p.producto_id for p in p_g.productos}) for p_g in grupo):
                    grupo.append(promo)
                    agregado = True
                    break
            if not agregado:
                grupos_conflicto.append([promo])

        # 3. REGLA 4: Si hay un grupo de conflicto con 3 o más promociones compitiendo A LA VEZ
        for grupo in grupos_conflicto:
            if len(grupo) >= 3:
                raise HTTPException(
                    status_code=400, 
                    detail="No se pueden combinar 3 o más promociones que comparten los mismos productos. Por favor, realice la venta por separado."
                )

        # 4. REGLAS 1 y 3: Resolver cada conflicto eligiendo la MEJOR promoción (la de mayor ahorro)
        promos_ganadoras = []
        for grupo in grupos_conflicto:
            if len(grupo) == 1:
                promos_ganadoras.append(grupo[0])
            else:
                mejor_promo = None
                menor_precio = Decimal("inf")

                for promo_candidata in grupo:
                    precio_simulado, _ = cls._aplicar_secuencia_promos(items_procesados, [promo_candidata])
                    if precio_simulado < menor_precio:
                        menor_precio = precio_simulado
                        mejor_promo = promo_candidata
                
                if mejor_promo:
                    promos_ganadoras.append(mejor_promo)

        # 5. Aplicamos definitivamente las promociones ganadoras
        _, items_optimizados = cls._aplicar_secuencia_promos(items_procesados, promos_ganadoras)

        # Reasignamos los subtotales al carrito final
        for item_orig, item_opt in zip(items_procesados, items_optimizados):
            item_orig["subtotal"] = item_opt["subtotal"]
            item_orig["precio_efectivo"] = item_opt["subtotal"] / item_orig["cantidad"]
            item_orig["promocion_aplicada"] = item_opt.get("promocion_aplicada") or item_opt.get("promocion")
              
    @staticmethod
    def registrar_venta(db: Session, venta_in: VentaCreate, usuario_id: int) -> Venta:
        # 1. Verificar consumo interno
        es_consumo_interno = any(
            pago.medio_pago.upper() == "CONSUMO_INTERNO" for pago in venta_in.pagos
        )

        # 2. Validar rol si es consumo interno
        if es_consumo_interno:
            usuario_actual = UsuarioRepository.obtener_por_id(db, usuario_id)
            if not usuario_actual or str(usuario_actual.role).lower() != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo los usuarios con rol ADMINISTRADOR pueden registrar consumos internos."
                )

        # 3. Buscar turno de caja abierto
        caja_abierta = CajaRepository.obtener_activa_por_usuario(db, usuario_id)
        if not caja_abierta:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No podés registrar la venta: No tenés un turno de caja abierto a tu nombre."
            )

        items_a_procesar = []

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

                # Inicializamos por defecto a precio de lista normal
                subtotal_inicial = producto.precio * detalle.cantidad
                costo_total = producto.costo * detalle.cantidad

                items_a_procesar.append({
                    "producto_obj": producto,
                    "cantidad": detalle.cantidad,
                    "costo_historico": producto.costo,
                    "costo_total": costo_total,
                    "subtotal": subtotal_inicial,
                    "precio_efectivo": producto.precio,
                })

            # 🌟 5. APLICAR LÓGICA DE PROMOCIONES A LOS SUBTOTALES
            VentaService._calcular_subtotales_con_promociones(db, items_a_procesar)

            # 6. Sumar totales finales ya calculados
            total_venta = Decimal("0.00")
            ganancia_total_venta = Decimal("0.00")

            for item in items_a_procesar:
                total_venta += item["subtotal"]
                ganancia_item = item["subtotal"] - item["costo_total"]
                ganancia_total_venta += ganancia_item

            # 7. Persistir cabecera de venta
            db_venta = VentaRepository.crear_cabecera(
                db=db,
                total=total_venta if not es_consumo_interno else Decimal("0.00"),
                ganancia_total=Decimal("0.00") if es_consumo_interno else ganancia_total_venta,
                caja_id=caja_abierta.id,
                usuario_id=usuario_id
            )

            # 8. Insertar renglones de detalle y descontar stock
            for item in items_a_procesar:
                nombre_promo = item.get("promocion_aplicada") or item.get("promocion") or None
                
                VentaRepository.crear_detalle(
                    db=db,
                    venta_id=db_venta.id,
                    producto_id=item["producto_obj"].id,
                    cantidad=item["cantidad"],
                    precio_historico=item["precio_efectivo"],  # Se guarda el precio unitario real cobrado
                    costo_historico=item["costo_historico"],
                    promocion_aplicada=nombre_promo
                )
                ProductoRepository.descontar_stock(
                    db=db,
                    producto=item["producto_obj"],
                    cantidad=item["cantidad"]
                )

            # 9. Registrar pagos
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
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None
    ) -> list[Venta]:
        
        dt_desde = None
        dt_hasta = None

        if fecha_desde:
            dt_desde = datetime.fromisoformat(fecha_desde)
            # Si sólo viene "YYYY-MM-DD", aseguramos el inicio del día
            if len(fecha_desde) <= 10:
                dt_desde = datetime.combine(dt_desde.date(), time.min)

        if fecha_hasta:
            dt_hasta = datetime.fromisoformat(fecha_hasta)
            # Si sólo viene "YYYY-MM-DD", aseguramos el final del día
            if len(fecha_hasta) <= 10:
                dt_hasta = datetime.combine(dt_hasta.date(), time.max)

        return VentaRepository.obtener_todas(
            db=db, 
            skip=skip, 
            limit=limit, 
            caja_id=caja_id, 
            fecha_desde=dt_desde, 
            fecha_hasta=dt_hasta
        )
        
    @staticmethod
    def cancelar_venta(db: Session, venta_id: int) -> Venta:
        # 1. Obtener la venta
        db_venta = VentaService.obtener_venta(db, venta_id)
        
        if db_venta.es_anulada:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La venta ya se encuentra anulada."
            )

        try:
            # 2. Devolver stock a cada producto
            for detalle in db_venta.detalles:
                if detalle.producto_id:
                    producto = ProductoRepository.obtener_por_id_para_update(db, detalle.producto_id)
                    if producto:
                        producto.stock += Decimal(str(detalle.cantidad))

            # 3. Marcar como anulada en lugar de eliminar
            db_venta.es_anulada = True
            
            db.commit()
            db.refresh(db_venta)
            return db_venta
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al anular la venta: {str(e)}"
            )