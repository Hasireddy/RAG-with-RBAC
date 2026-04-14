from datetime import datetime
from pydantic import BaseModel, Field

# pydantic models for API validation

class EmployeeCreate(BaseModel):
    """Model for creating a Department"""

    emp_name:str= Field(
        min_length=3,
        max_length=50,
        description="Employee name (alphabets only)",
    )
    job_title:str= Field(
        min_length=3,
        max_length=50,
        description="Job title (alphabets only)",
    )



class EmployeeResponse(BaseModel):
    emp_id: int
    emp_name: str
    job_title: str
    dept_id: int
    company_id: int
    role_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True
