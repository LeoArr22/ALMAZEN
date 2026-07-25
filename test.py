import pytest
from starlette.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Importamos la app de FastAPI y la Base
from src.main import app
from src.config.database import Base, get_db

# ==========================================
# 🛠️ CONFIGURACIÓN DE BASE DE DATOS EN MEMORIA
# ==========================================
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        # Verifica que la sesión siga activa antes de intentar cerrarla
        if db.is_active:
            db.close()

# Sobrescribimos la dependencia de base de datos para usar la de memoria
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app=app)

# ==========================================
# 🚀 SECUENCIA DE PRUEBAS DEL SISTEMA
# ==========================================

def test_flujo_completo_sistema():
    # 0. Crear tablas vacías en la BD de prueba
    Base.metadata.create_all(bind=engine)

    print("\n--- 1. PROBANDO CREACIÓN DE USUARIOS ---")
    
    # 1a. Registrar primer admin (como no hay auth previa en BD vacía, este es el admin inicial)
    # Nota: si tu endpoint /usuarios/registrar pide token admin, creamos usuario directo en la BD o llamamos el endpoint.
    from src.models.usuario import Usuario
    from src.config.security import obtener_password_hash
    
    db = TestingSessionLocal()
    admin_user = Usuario(
        username="admin_test",
        password_hashed=obtener_password_hash("admin123"),
        role="ADMIN"
    )
    vendedor_user = Usuario(
        username="vendedor_1",
        password_hashed=obtener_password_hash("vendedor123"),
        role="VENDEDOR"
    )
    db.add(admin_user)
    db.add(vendedor_user)
    db.commit()
    db.close()
    print("✅ Usuarios 'admin_test' y 'vendedor_1' creados con éxito.")

    # ------------------------------------------
    print("\n--- 2. PROBANDO AUTENTICACIÓN (LOGIN) ---")
    
    # Login Admin
    res_login_admin = client.post(
        "/usuarios/login",
        data={"username": "admin_test", "password": "admin123"}
    )
    assert res_login_admin.status_code == 200
    token_admin = res_login_admin.json()["access_token"]
    headers_admin = {"Authorization": f"Bearer {token_admin}"}
    print("✅ Login Admin correcto. Token JWT obtenido.")

    # Login Vendedor
    res_login_vend = client.post(
        "/usuarios/login",
        data={"username": "vendedor_1", "password": "vendedor123"}
    )
    assert res_login_vend.status_code == 200
    token_vend = res_login_vend.json()["access_token"]
    headers_vend = {"Authorization": f"Bearer {token_vend}"}
    print("✅ Login Vendedor correcto. Token JWT obtenido.")

    # ------------------------------------------
    print("\n--- 3. PROBANDO GESTIÓN DE PRODUCTOS ---")
    
    # Crear Producto 1 (Yerba)
    prod_1 = {
        "nombre": "Yerba Mate 1kg",
        "descripcion": "Yerba mate elaborada con palo",
        "categoria": "Almacen",
        "stock": 20,
        "costo": 1500.00,
        "precio": 2500.00,
        "codigo_barras": "7791234567890"
    }
    res_prod1 = client.post("/productos/", json=prod_1, headers=headers_admin)
    assert res_prod1.status_code == 201
    prod1_data = res_prod1.json()
    prod1_id = prod1_data["id"]
    print(f"✅ Producto creado: {prod1_data['nombre']} (ID: {prod1_id}, Stock: {prod1_data['stock']})")

    # Validar regla de negocio: No se puede crear producto con precio < costo
    prod_invalido = {
        "nombre": "Producto Fundición",
        "categoria": "Varios",
        "stock": 10,
        "costo": 2000.00,
        "precio": 1000.00 # ❌ Error: menor al costo
    }
    res_inv = client.post("/productos/", json=prod_invalido, headers=headers_admin)
    assert res_inv.status_code == 400
    print("✅ Bloqueo correcto: Rechazó producto con precio menor al costo.")

    # ------------------------------------------
    print("\n--- 4. PROBANDO REGLAS DE APERTURA DE CAJA ---")

    # Intentar vender SIN caja abierta
    venta_sin_caja = {
        "detalles": [{"producto_id": prod1_id, "cantidad": 2}]
    }
    res_v_error = client.post("/ventas/", json=venta_sin_caja, headers=headers_vend)
    assert res_v_error.status_code == 400
    print("✅ Bloqueo correcto: Se impidió vender sin caja abierta.")

    # Abrir Caja para el Vendedor
    caja_in = {"monto_inicial": 5000.00}
    res_caja = client.post("/cajas/", json=caja_in, headers=headers_vend)
    assert res_caja.status_code == 201
    caja_data = res_caja.json()
    print(f"✅ Caja abierta ID {caja_data['id']} con monto inicial: ${caja_data['monto_inicial']}")

    # ------------------------------------------
    print("\n--- 5. PROBANDO PROCESAMIENTO DE VENTAS Y STOCK ---")

    # Realizar Venta de 3 Yerbas
    venta_valida = {
        "detalles": [{"producto_id": prod1_id, "cantidad": 3}]
    }
    res_venta = client.post("/ventas/", json=venta_valida, headers=headers_vend)
    assert res_venta.status_code == 201
    v_data = res_venta.json()
    
    # 3 yerbas * $2500 = $7500 total
    # Ganancia: (2500 - 1500) * 3 = $3000
    assert float(v_data["total"]) == 7500.00
    assert float(v_data["ganancia_total"]) == 3000.00
    print(f"✅ Venta registrada N° {v_data['id']}: Total ${v_data['total']} | Ganancia ${v_data['ganancia_total']}")

    # Verificar que el stock haya bajado de 20 a 17
    res_prod_check = client.get(f"/productos/{prod1_id}", headers=headers_vend)
    assert res_prod_check.json()["stock"] == 17
    print("✅ Descuento de stock verificado: Quedan 17 unidades en inventario.")

    # Validar exceso de stock
    venta_exceso = {
        "detalles": [{"producto_id": prod1_id, "cantidad": 100}] # ❌ No hay 100
    }
    res_exceso = client.post("/ventas/", json=venta_exceso, headers=headers_vend)
    assert res_exceso.status_code == 400
    print("✅ Bloqueo correcto: Impidió vender más unidades de las disponibles en stock.")

    # ------------------------------------------
    print("\n--- 6. PROBANDO CIERRE DE CAJA Y ARQUEO ---")

    # Cierre de Caja
    # Inicial: $5000 + Venta: $7500 = Esperado: $12500
    # Contamos físicamente $12500 en el cajón
    cierre_in = {"monto_final_real": 12500.00}
    res_cierre = client.put("/cajas/cerrar", json=cierre_in, headers=headers_vend)
    assert res_cierre.status_code == 200
    cierre_data = res_cierre.json()

    assert cierre_data["estado"] == "CERRADA"
    assert float(cierre_data["monto_final_estimado"]) == 12500.00
    assert float(cierre_data["monto_final_real"]) == 12500.00
    print(f"✅ Caja CERRADA con éxito. Arqueo perfecto sin diferencias de dinero.")

    print("\n==============================================")
    print(" 🎉 ¡TODAS LAS PRUEBAS PASARON SATISFACTORIAMENTE!")
    print("==============================================\n")

if __name__ == "__main__":
    test_flujo_completo_sistema()