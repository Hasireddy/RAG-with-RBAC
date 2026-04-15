from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re

# pydantic models for API validation

class DepartmentCreate(BaseModel):
    """Model for creating a Department"""

    dept_name: str = Field(
        min_length=3,
        max_length=50,
        description="Department name (alphabets only)",
    )
    dept_code: str= Field(
        min_length=2,
        max_length=20,
        description="Department Code (alphabets only)",
    )

    @field_validator("dept_name")
    @classmethod
    def validate_name(cls, v):
        if not re.match(r"^[A-Za-z ]+$", v):
            raise ValueError("Department name must contain only alphabets")
        return v

    @field_validator("dept_code")
    @classmethod
    def validate_code(cls, v):
        if not re.match(r"^[A-Z0-9]+$", v):
            raise ValueError("Department code must be uppercase alphanumeric")
        return v

class DepartmentResponse(BaseModel):
    """Department response model"""
    id: int
    dept_name: str
    dept_code: str
    created_at: datetime
    company_id: int

    model_config = ConfigDict(extra="forbid")


class DepartmentUpdate(BaseModel):
    """Department update model to update a department"""

    dept_name:Optional[str] = None
    dept_code:Optional[str] = None

    model_config = {"extra": "forbid"}

