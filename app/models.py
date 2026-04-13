from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

# pydantic models for API validation

class CompanyCreate(BaseModel):
    """Model for creating Company"""

    company_name:str
    domain:str
    location:str


class CompanyResponse(BaseModel):
    id: int
    company_name: str
    domain: str
    location: str
    created_at: datetime

    class Config:
        from_attributes = True




class DepartmentCreate(BaseModel):
    """Model for creating a Department"""

    dept_name:str


class DepartmentResponse(BaseModel):
    dept_id: int
    dept_name: str
    created_at: datetime
    company_id: int

    class Config:
        from_attributes = True




class EmployeeCreate(BaseModel):
    """Model for creating a Department"""

    emp_name:str
    job_title:str



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
    role_name:str


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






