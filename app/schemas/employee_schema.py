from datetime import datetime
from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional, List
import re

# pydantic model for API validation

class EmployeeCreate(BaseModel):
    """Schema for creating an Employee"""

    emp_name: str= Field(
        min_length=3,
        max_length=50,
        description="Employee name (alphabets only)",
    )

    job_title:str= Field(
        min_length=3,
        max_length=50,
        description="Job title (alphabets only)",
    )

    email: EmailStr = Field(
        description="Employee email (must be unique)"
    )
    company_id: int
    dept_id: List

    password: str = Field(
        min_length=8,
        max_length=128,
        description="Employee account password"
    )

    @field_validator("emp_name", "job_title")
    @classmethod
    def validate_alpha(cls, v):
        if not re.match(r"^[A-Za-z ]+$", v):
            raise ValueError("Only alphabets and spaces allowed")
        return v


class EmployeeResponse(BaseModel):
    """Employee Response Model"""

    emp_id: int
    emp_name: str
    job_title: str
    email: EmailStr
    dept_id: int
    company_id: int
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class EmployeeUpdate(BaseModel):
    """Employee update model"""

    emp_name:Optional[str] = None
    job_title: Optional[str] = None
    email:Optional[EmailStr] = None
    company_id: Optional[int] = None
    dept_id: Optional[int] = None

    model_config = {"extra": "forbid"}
