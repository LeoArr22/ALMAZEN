import pytest
from src.main import app
from src.dependencies.auth import get_current_user
from src.dependencies.roles import RoleChecker
from src.models.usuario import Usuario

@pytest.fixture
def mock_entorno_venta():
    vendedor = Usuario(id=1, username="vendedor_pos", role="vendedor")
    admin = Usuario(id=2, username="admin_pos", role="admin")
    
    app.dependency_overrides[get_current_user] = lambda: vendedor
    app.dependency_overrides[RoleChecker(["ADMIN", "admin"])] = lambda: admin
    yield
    app.dependency_overrides.clear()


def test_vendedor_no_puede_anular_venta(client):
    """Un usuario común no debe poder anular una venta existente."""
    vendedor = Usuario(id=1, username="vendedor_pos", role="vendedor")
    app.dependency_overrides[get_current_user] = lambda: vendedor
    
    # Intentar anular venta #1
    respuesta = client.post("/ventas/1/anular")
    assert respuesta.status_code in [401, 403]
    app.dependency_overrides.clear()
    
    
def test_registrar_venta_y_descontar_stock(client, override_admin):
    # 1. Abrir caja previa necesaria para vender
    client.post("/cajas/", json={"monto_inicial": 5000.0})

    # 2. Crear producto con stock 10
    prod_res = client.post("/productos/", json={
        "nombre": "Yerba Mate 500g",
        "categoria": "Almacen",
        "stock": 10.0,
        "costo": 800.0,
        "precio": 1200.0,
        "codigo_barras": "7791234123412"
    })
    prod_id = prod_res.json()["id"]

    # 3. Registrar venta con la clave 'detalles'
    payload_venta = {
        "detalles": [
            {
                "producto_id": prod_id, 
                "cantidad": 2.0
            }
        ],
        "pagos": [
            {"medio_pago": "Efectivo", "monto": 1400.0},
            {"medio_pago": "Tarjetas", "monto": 1000.0}
        ]
    }
    res_venta = client.post("/ventas/", json=payload_venta)
    assert res_venta.status_code in [200, 201]

    # 4. Verificar descuento de stock
    res_prod = client.get("/productos/codigo/7791234123412")
    assert float(res_prod.json()["stock"]) == 8.0