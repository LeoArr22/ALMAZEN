import pytest
from src.main import app
from src.dependencies.auth import get_current_user
from src.models.usuario import Usuario

@pytest.fixture
def override_usuario_autenticado():
    usuario = Usuario(id=1, username="vendedor1", role="vendedor")
    app.dependency_overrides[get_current_user] = lambda: usuario
    yield usuario
    app.dependency_overrides.clear()

def test_flujo_abrir_y_cerrar_caja(client, override_usuario_autenticado):
    # 1. Abrir Caja
    res_abrir = client.post("/cajas/", json={"monto_inicial": 5000.0})
    assert res_abrir.status_code == 201
    assert float(res_abrir.json()["monto_inicial"]) == 5000.0

    # 2. Consultar Caja Activa
    res_activa = client.get("/cajas/activa")
    assert res_activa.status_code == 200
    assert res_activa.json()["estado"] == "ABIERTA"

    # 3. Cerrar Caja
    res_cerrar = client.post("/cajas/cerrar", json={"monto_final_real": 5000.0})
    assert res_cerrar.status_code == 200
    
def test_cerrar_caja_con_desglose_pagos(client, override_usuario_autenticado):
    # 1. Abrir caja
    client.post("/cajas/", json={"monto_inicial": 5000.0})

    # 2. Cerrar caja enviando pagos agregados
    payload = {
        "monto_final_real": 15000.0,
        "pagos": [
            {"medio_pago": "Efectivo", "monto": 10000.0},
            {"medio_pago": "Transferencia", "monto": 5000.0}
        ]
    }
    res = client.post("/cajas/cerrar", json=payload)
    assert res.status_code == 200