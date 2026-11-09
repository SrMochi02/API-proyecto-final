from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.schemas.role import RoleResponse


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Nombre de usuario unico")
    email: EmailStr = Field(..., description="Correo electronico valido")
    full_name: Optional[str] = Field(None, max_length=100, description="Nombre completo")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100, description="Contraseña de al menos 6 caracteres")
    role_id: int = Field(..., gt=0, description="ID del rol asignado")


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=6, max_length=100)
    is_active: Optional[bool] = None
    role_id: Optional[int] = Field(None, gt=0)


class UserResponse(UserBase):
    id: int
    is_active: bool
    role_id: int
    created_at: datetime
    role: Optional[RoleResponse] = None

    model_config = ConfigDict(from_attributes=True)
