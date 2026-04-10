from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

# pydantic models for API validation

class Company(BaseModel):
    """Model for creating Company"""

    id:int
    company_name:str
    domain:str
    location:str
    created_at: datetime



class Department(BaseModel):
    """Model for creating a Department"""

    dept_id:int
    dept_name:str
    created_at: datetime



class Employee(BaseModel):
    """Model for creating a Department"""

    emp_id:int
    emp_name:str
    job_title:str
    manager_id:int | None = None
    created_at: datetime


