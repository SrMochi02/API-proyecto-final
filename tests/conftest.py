import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.seeds import seed_database

# Motor de prueba en memoria SQLite aislado
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine_test)
    # Poblar datos base para las pruebas
    from app.core.security import get_password_hash
    from app.models.role import Role
    from app.models.user import User
    from app.models.author import Author
    from app.models.category import Category
    from app.models.book import Book

    db = TestingSessionLocal()
    # Roles
    r_admin = Role(id=1, name="ADMINISTRADOR", description="Admin")
    r_biblio = Role(id=2, name="BIBLIOTECARIO", description="Biblio")
    r_user = Role(id=3, name="USUARIO", description="User")
    db.add_all([r_admin, r_biblio, r_user])
    db.commit()

    # Users
    u_admin = User(
        id=1, username="admin_test", email="admin@test.com",
        hashed_password=get_password_hash("admin123"), role_id=1, is_active=True
    )
    u_biblio = User(
        id=2, username="biblio_test", email="biblio@test.com",
        hashed_password=get_password_hash("biblio123"), role_id=2, is_active=True
    )
    u_normal = User(
        id=3, username="user_test", email="user@test.com",
        hashed_password=get_password_hash("user123"), role_id=3, is_active=True
    )
    db.add_all([u_admin, u_biblio, u_normal])
    db.commit()

    # Author & Category
    author = Author(id=1, nombre="Gabriel Garcia Marquez", nacionalidad="Colombiana")
    category = Category(id=1, nombre="Realismo Magico", descripcion="Novelas")
    db.add_all([author, category])
    db.commit()

    # Book with 1 exemplar (for availability tests)
    book = Book(
        id=1, titulo="Cien años de soledad", isbn="978-0307474728",
        anio_publicacion=1967, autor_id=1, categoria_id=1,
        ejemplares_totales=1, ejemplares_disponibles=1, disponible=True
    )
    db.add(book)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
