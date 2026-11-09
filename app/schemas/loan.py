from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.user import UserResponse
from app.schemas.book import BookResponse


class LoanCreate(BaseModel):
    libro_id: int = Field(..., gt=0, description="ID del libro a solicitar en prestamo")
    fecha_devolucion_esperada: datetime = Field(..., description="Fecha limite esperada para la devolucion")
    observaciones: Optional[str] = Field(None, max_length=255, description="Observaciones opcionales del prestamo")


class LoanReturn(BaseModel):
    observaciones: Optional[str] = Field(None, max_length=255, description="Observaciones sobre el estado del libro al devolver")


class LoanResponse(BaseModel):
    id: int
    usuario_id: int
    libro_id: int
    fecha_prestamo: datetime
    fecha_devolucion_esperada: datetime
    fecha_devolucion_real: Optional[datetime] = None
    estado: str
    observaciones: Optional[str] = None
    user: Optional[UserResponse] = None
    book: Optional[BookResponse] = None

    model_config = ConfigDict(from_attributes=True)
