from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AuthorBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre del autor")
    nacionalidad: Optional[str] = Field(None, max_length=80, description="Nacionalidad del autor")
    biografia: Optional[str] = Field(None, description="Biografia resumida")


class AuthorCreate(AuthorBase):
    pass


class AuthorUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    nacionalidad: Optional[str] = Field(None, max_length=80)
    biografia: Optional[str] = None


class AuthorResponse(AuthorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
