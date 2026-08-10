import pytest
from src.main import app
from src.dependencies.auth import get_current_user
from src.models.usuario import Usuario

def test_libro_diario_requiere_admin(client):
    respuesta = client.get("/libro-diario/?periodo=dia")
    assert respuesta.status_code in [401, 403]

def test_libro_diario_consulta_admin(client):
    admin = Usuario(id=1, username="admin_boss", role="admin")
    app.dependency_overrides[get_current_user] = lambda: admin

    respuesta = client.get("/libro-diario/?periodo=dia")
    assert respuesta.status_code == 200
    
    app.dependency_overrides.clear()