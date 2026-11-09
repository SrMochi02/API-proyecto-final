from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.author import AuthorResponse
from app.schemas.category import CategoryResponse


class BookBase(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=150, description="Titulo del libro")
    isbn: str = Field(..., min_length=10, max_length=20, description="Codigo ISBN unico")
    anio_publicacion: Optional[int] = Field(None, ge=1000, le=2100, description="Año de publicacion valido")
    autor_id: int = Field(..., gt=0, description="ID del autor existente")
    categoria_id: int = Field(..., gt=0, description="ID de la categoria existente")
    ejemplares_totales: int = Field(1, ge=1, description="Cantidad total de ejemplares (minimo 1)")


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=1, max_length=150)
    isbn: Optional[str] = Field(None, min_length=10, max_length=20)
    anio_publicacion: Optional[int] = Field(None, ge=1000, le=2100)
    autor_id: Optional[int] = Field(None, gt=0)
    categoria_id: Optional[int] = Field(None, gt=0)
    ejemplares_totales: Optional[int] = Field(None, ge=1)


class BookResponse(BaseModel):
    id: int
    titulo: str
    isbn: str
    anio_publicacion: Optional[int] = None
    autor_id: int
    categoria_id: int
    ejemplares_totales: int
    ejemplares_disponibles: int
    disponible: bool
    created_at: datetime
    author: Optional[AuthorResponse] = None
    category: Optional[CategoryResponse] = None

    model_config = ConfigDict(from_attributes=True)
