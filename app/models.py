from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

# pydantic models for API validation

class CompanyCreate(BaseModel):
    """Model for creating Company"""

    company_name:str = Field(
        min_length=3,
        max_length=50,
        description="Company name (alphabets only)",
    )
    domain:str
    location:str


class CompanyResponse(BaseModel):
    """Company response model"""

    id: int
    company_name: str
    domain: str
    location: str
    created_at: datetime

    class Config:
        from_attributes = True




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



class PermissionCreate(BaseModel):
    permission_name:str



class PermissionResponse(BaseModel):
    id: int
    permission_name: str

    class Config:
        from_attributes = True






