from pydantic import BaseModel

# pydantic models for API validation

class Company(BaseModel):
    id:int
    company_name:str
    domain:str
    location:str



class Department(BaseModel):
    dept_id:int
    dept_name:str
    company_id:int


class Employee(BaseModel):
    emp_id:int
    emp_name:str
    job_title:str
    manager_id:int
    dept_id:int
    company_id:int

