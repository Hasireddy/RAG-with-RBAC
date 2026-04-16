from datetime import datetime
from pydantic import BaseModel, Field, field_validator, EmailStr
import re

# pydantic model for API validation

class EmployeeCreate(BaseModel):
    """Model for creating an Employee"""

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

    @field_validator("emp_name", "job_title")
    @classmethod
    def validate_alpha(cls, v):
        if not re.match(r"^[A-Za-z ]+$", v):
            raise ValueError("Only alphabets and spaces allowed")
        return v


class EmployeeResponse(BaseModel):
    emp_id: int
    emp_name: str
    job_title: str
    email: str
    dept_id: int
    company_id: int
    role_id: int | None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
