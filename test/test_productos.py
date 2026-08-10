import pytest
from src.main import app
from src.dependencies.auth import get_current_user
from src.models.usuario import Usuario

@pytest.fixture
def override_admin():
    admin_user = Usuario(id=1, username="admin_test", role="admin")
    app.dependency_overrides[get_current_user] = lambda: admin_user
    yield admin_user
    app.dependency_overrides.clear()

def test_crear_producto_como_admin(client, override_admin):
    payload = {
        "nombre": "Coca Cola 1.5L",
        "categoria": "Bebidas",
        "stock": 20.0,
        "costo": 1000.0,
        "precio": 1500.0,
        "codigo_barras": "7791234567890"  # 13 dígitos
    }
    respuesta = client.post("/productos/", json=payload)
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["nombre"] == "Coca Cola 1.5L"
    assert datos["codigo_barras"] == "7791234567890"

def test_crear_producto_sin_permisos_falla(client):
    payload = {
        "nombre": "Producto No Autorizado",
        "categoria": "Varios",
        "costo": 100.0,
        "precio": 200.0,
        "codigo_barras": "7791111111111"
    }
    respuesta = client.post("/productos/", json=payload)
    assert respuesta.status_code in [401, 403]

def test_obtener_producto_por_codigo(client, override_admin):
    # 1. Crear producto con código válido de 13 dígitos
    codigo_valido = "7798888999900"
    res_crear = client.post("/productos/", json={
        "nombre": "Galletitas Marolio",
        "categoria": "Almacén",
        "stock": 10.0,
        "costo": 200.0,
        "precio": 350.0,
        "codigo_barras": codigo_valido
    })
    assert res_crear.status_code == 201

    # 2. Consultar por código de barras
    respuesta = client.get(f"/productos/codigo/{codigo_valido}")
    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == "Galletitas Marolio"