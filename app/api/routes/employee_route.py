from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.schemas.employee_schema import EmployeeCreate, EmployeeResponse
from app.database.session import get_db
from app.models.employee_model import EmployeeDB

router = APIRouter()



# Get all employees
@router.get("/employees", response_model=List[EmployeeResponse])
def get_employees(db: Session = Depends(get_db)):
    employees = db.query(EmployeeDB).all()
    if not employees:
        raise HTTPException(
            status_code=404,
            detail="Employees not found. Please create a new employee"
        )
    return employees


# Create an employee
@router.post("/employees")
def add_employee():
    pass


# Update an employee
@router.put("/employees")
def update_employee():
    pass


# Delete an employee
@router.delete("/employees")
def delete_employee():
    pass


# Get employee by id
@router.get("/employee/id")
def get_employee_by_id():
    pass


# Get employees by department
@router.get("/employees/dept")
def get_employees_by_department():
    pass


