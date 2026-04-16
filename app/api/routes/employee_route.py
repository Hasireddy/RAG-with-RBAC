from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.schemas.employee_schema import EmployeeCreate, EmployeeResponse, EmployeeUpdate
from app.database.session import get_db
from app.models.employee_model import EmployeeDB
from app.models.company_model import CompanyDB
from app.models.department_model import DepartmentDB
from app.models.role_model import RoleDB

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


# Create a new employee, link them to the company, link them to a department, link them to a role
# Save everything in DB
@router.post("/employees", response_model=EmployeeResponse)
def add_employee(employee:EmployeeCreate, db: Session = Depends(get_db)):
    # Check if employee already exists
    existing_employee = db.query(EmployeeDB).filter(EmployeeDB.email == employee.email).first()

    if existing_employee:
        raise HTTPException(
            status_code=400,
            detail="Employee already exists"
        )

    # Validate Company - Check if company exists
    company = db.query(CompanyDB).filter(CompanyDB.id == employee.company_id).first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Check if department exists
    department = db.query(DepartmentDB).filter(DepartmentDB.id == employee.dept_id).first()

    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    # Check a role if it exists to assign to the employee
    #role = db.query(RoleDB).filter(RoleDB.id == employee.role_id).first()

    #if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Create a new employee
    new_employee = EmployeeDB(
        emp_name=employee.emp_name,
        email=employee.email,
        job_title=employee.job_title,
        company_id=employee.company_id,
        dept_id=employee.dept_id,
        role_id=employee.role_id
    )

    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)

    return new_employee



# Update an employee
@router.put("/employees/{emp_id}", response_model=EmployeeResponse)
def update_employee(emp_id: int, employee : EmployeeUpdate, db: Session = Depends(get_db)):

    # Find employee with given id
    emp_to_update = db.query(EmployeeDB).filter(EmployeeDB.emp_id == emp_id).first()

    if not emp_to_update:
        raise HTTPException(
            status_code=400,
            detail="Employee with given id not found"
        )


    # 2. Update only provided fields
    # for field, value in employee.dict(exclude_unset=True).items():
        setattr(emp_to_update, field, value)
    if employee.emp_name is not None:
        emp_to_update.emp_name = employee.emp_name

    if employee.job_title is not None:
        emp_to_update.job_title = employee.job_title

    if employee.email is not None:
        emp_to_update.email = employee.email

    if employee.company_id is not None:
        emp_to_update.company_id = employee.company_id

    if employee.dept_id is not None:
        emp_to_update.dept_id = employee.dept_id

    if employee.role_id is not None:
        emp_to_update.role_id = employee.role_id

    db.commit()
    db.refresh(emp_to_update)

    return emp_to_update



# Delete an employee
@router.delete("/employees/{emp_id}")
def delete_employee(emp_id: int, db: Session = Depends(get_db)):
    emp_to_delete = db.query(EmployeeDB).filter(EmployeeDB.emp_id == emp_id).first()

    if not emp_to_delete:
        raise HTTPException(
            status_code=400,
            detail="Employee with given id not found"
        )

    db.delete(emp_to_delete)
    db.commit()
    return {"message": f"Employee with id {emp_id} deleted successfully"}


# Get employee by id
@router.get("/employee/id")
def get_employee_by_id():
    pass


# Get employees by department
@router.get("/employees/dept")
def get_employees_by_department():
    pass


