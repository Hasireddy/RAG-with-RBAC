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
def update_employee(emp_id: int, payload : EmployeeUpdate, db: Session = Depends(get_db)):

    # Find employee with given id
    emp_to_update = db.query(EmployeeDB).filter(EmployeeDB.emp_id == emp_id).first()

    if not emp_to_update:
        raise HTTPException(
            status_code=400,
            detail="Employee with given id not found"
        )

    # Convert request to dict(only sent fields)
    update_data = payload.model_dump(exclude_unset=True)

    # Validate email uniqueness
    if "email" in update_data:
        existing = db.query(EmployeeDB).filter(EmployeeDB.email == update_data["email"]).first()
        if existing and existing.emp_id != emp_id:
            raise HTTPException(status_code=400, detail="Email already in use")

        # 4. Validate foreign keys (if provided)

        if "company_id" in update_data:
            company = db.query(CompanyDB).filter(CompanyDB.id == update_data["company_id"]).first()
            if not company:
                raise HTTPException(status_code=404, detail="Company not found")

        if "dept_id" in update_data:
            department = db.query(DepartmentDB).filter(DepartmentDB.id == update_data["dept_id"]).first()
            if not department:
                raise HTTPException(status_code=404, detail="Department not found")

        #if "role_id" in update_data:
            #role = db.query(RoleDB).filter(RoleDB.id == update_data["role_id"]).first()
            #if not role:
                raise HTTPException(status_code=404, detail="Role not found")

    for key, value in update_data.items():
        setattr(emp_to_update, key, value)

    db.commit()
    db.refresh(emp_to_update)

    return emp_to_update



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


