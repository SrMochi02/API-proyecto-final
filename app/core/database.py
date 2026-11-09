from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# Ajuste de argumentos de conexion segun el motor (SQLite o PostgreSQL)
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
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
