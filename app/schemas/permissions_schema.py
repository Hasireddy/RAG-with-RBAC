from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

# pydantic models for API validation


class PermissionCreate(BaseModel):
    permission_name:str



class PermissionResponse(BaseModel):
    id: int
    permission_name: str

    class Config:
        from_attributes = True
