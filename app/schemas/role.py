from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="Nombre del rol")
    description: Optional[str] = Field(None, max_length=255, description="Descripcion del rol")


class RoleCreate(RoleBase):
    pass


class RoleResponse(RoleBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
