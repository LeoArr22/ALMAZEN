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