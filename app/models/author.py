from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Author(Base):
    __tablename__ = "autores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, index=True)
    nacionalidad = Column(String(80), nullable=True)
    biografia = Column(Text, nullable=True)

    # Relacion uno a muchos con libros
    books = relationship("Book", back_populates="author", cascade="save-update")
