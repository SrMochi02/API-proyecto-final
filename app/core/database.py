from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# Ajuste de argumentos de conexion y driver segun el motor (SQLite o PostgreSQL)
database_url = settings.DATABASE_URL
connect_args = {}
if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif database_url.startswith("postgresql://"):
    try:
        import psycopg  # noqa: F401
    except ImportError:
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(
    database_url,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Generador de sesion de base de datos para inyeccion de dependencias en FastAPI.
    Garantiza el cierre seguro de la conexion tras completar la peticion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
