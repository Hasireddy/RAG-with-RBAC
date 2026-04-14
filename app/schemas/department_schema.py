from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

# pydantic models for API validation

class DepartmentCreate(BaseModel):
    """Model for creating a Department"""

    dept_name: str = Field(
        min_length=3,
        max_length=50,
        description="Department name (alphabets only)",
    )
    dept_code: str= Field(
        min_length=3,
        max_length=20,
        description="Department Code (alphabets only)",
    )


class DepartmentResponse(BaseModel):
    """Department response model"""

    dept_id: int
    dept_name: str
    dept_code: str= Field(min_length=2, max_length=10)
    created_at: datetime
    company_id: int

    class Config:
        from_attributes = True


class DepartmentUpdate(BaseModel):
    """Department update model to update a department"""

    dept_name:Optional[str] = None
    dept_code:Optional[str] = None

    model_config = {"extra": "forbid"}

