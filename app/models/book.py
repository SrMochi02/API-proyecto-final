from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Book(Base):
    __tablename__ = "libros"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(150), nullable=False, index=True)
    isbn = Column(String(20), unique=True, nullable=False, index=True)
    anio_publicacion = Column(Integer, nullable=True)
    
    # Llaves foraneas a autor y categoria con proteccion de integridad
    autor_id = Column(Integer, ForeignKey("autores.id", ondelete="RESTRICT"), nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id", ondelete="RESTRICT"), nullable=False)
    
    ejemplares_totales = Column(Integer, default=1, nullable=False)
    ejemplares_disponibles = Column(Integer, default=1, nullable=False)
    disponible = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones
    author = relationship("Author", back_populates="books")
    category = relationship("Category", back_populates="books")
    loans = relationship("Loan", back_populates="book")
