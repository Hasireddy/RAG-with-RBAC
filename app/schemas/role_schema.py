from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

# pydantic models for API validation


class RoleCreate(BaseModel):
    role_name:str= Field(
        min_length=3,
        max_length=50,
        description="Role (alphabets only)",
    )


class RoleResponse(BaseModel):
    id: int
    role_name: str

    class Config:
        from_attributes = True


