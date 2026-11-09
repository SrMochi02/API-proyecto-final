from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Loan(Base):
    __tablename__ = "prestamos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    libro_id = Column(Integer, ForeignKey("libros.id", ondelete="RESTRICT"), nullable=False)
    
    fecha_prestamo = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_devolucion_esperada = Column(DateTime(timezone=True), nullable=False)
    fecha_devolucion_real = Column(DateTime(timezone=True), nullable=True)
    
    # Estados permitidos: ACTIVO, DEVUELTO, VENCIDO
    estado = Column(String(20), default="ACTIVO", nullable=False, index=True)
    observaciones = Column(String(255), nullable=True)

    # Relaciones
    user = relationship("User", back_populates="loans")
    book = relationship("Book", back_populates="loans")
