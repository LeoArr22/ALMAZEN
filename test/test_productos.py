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
    
def test_actualizar_producto_y_normalizar_categoria(client, override_admin):
    # 1. Crear producto base
    res_crear = client.post("/productos/", json={
        "nombre": "Galletitas Dulces",
        "categoria": "Almacen",
        "stock": 10.0,
        "costo": 500.0,
        "precio": 800.0,
        "codigo_barras": "7790000000001"
    })
    assert res_crear.status_code == 201
    prod_id = res_crear.json()["id"]

    # 2. Actualizar enviando categoría con tildes/minusculas y floats
    payload_update = {
        "nombre": "Galletitas Dulces Modificadas",
        "codigo_barras": None,
        "descripcion": "Paquete x 400g",
        "categoria": "almacén y golosínas",  # Prueba de normalización
        "stock": 150.0,
        "costo": 650.50,
        "precio": 1000.0
    }
    res_put = client.put(f"/productos/{prod_id}", json=payload_update)
    assert res_put.status_code == 200

    datos = res_put.json()
    assert datos["nombre"] == "Galletitas Dulces Modificadas"
    assert datos["codigo_barras"] is None
    assert datos["categoria"] == "Almacen y golosinas"  # Verifica normalización (Title Case sin tildes)
    assert float(datos["stock"]) == 150.0
    assert float(datos["costo"]) == 650.50
    assert float(datos["precio"]) == 1000.0

def test_actualizar_producto_inexistente(client, override_admin):
    payload = {
        "nombre": "Fantasma",
        "categoria": "Varios",
        "stock": 1.0,
        "costo": 10.0,
        "precio": 20.0
    }
    res = client.put("/productos/99999", json=payload)
    assert res.status_code == 404
    