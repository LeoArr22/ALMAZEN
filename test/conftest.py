import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config.database import Base, get_db
from src.main import app  # 👈 Importamos app desde src.main
from src.models.usuario import Usuario
from src.dependencies.auth import get_current_user

# Base de datos SQLite exclusiva para la ejecución de tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_almazen.db"

engine_test = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Crea la estructura de tablas antes de correr los tests y la elimina al finalizar."""
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def db_session():
    """Proveedora de sesiones de base de datos aisladas por test."""
    connection = engine_test.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """Cliente HTTP simulado con inyección de la base de datos de pruebas."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    
@pytest.fixture
def override_admin(db_session):
    """Crea un usuario admin real en la BD de pruebas y overridea la autenticación."""
    admin_user = Usuario(
        id=1,
        username="admin",
        password_hashed="fake_hashed_password_123",  # 👈 Campo obligatorio agregado
        role="admin",
        activo=True
    )
    db_session.add(admin_user)
    db_session.commit()
    db_session.refresh(admin_user)

    app.dependency_overrides[get_current_user] = lambda: admin_user
    yield admin_user
    app.dependency_overrides.clear()