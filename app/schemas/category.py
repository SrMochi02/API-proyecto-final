from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=80, description="Nombre de la categoria")
    descripcion: Optional[str] = Field(None, max_length=255, description="Descripcion de la categoria")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=80)
    descripcion: Optional[str] = Field(None, max_length=255)


class CategoryResponse(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
