from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base


class Category(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(80), unique=True, nullable=False, index=True)
    descripcion = Column(String(255), nullable=True)

    # Relacion uno a muchos con libros
    books = relationship("Book", back_populates="category", cascade="save-update")
