from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas.employee_schema import EmployeeCreate, EmployeeResponse, EmployeeUpdate
from app.database.session import get_db
from app.models.employee_model import EmployeeDB
from app.models.company_model import CompanyDB
from app.models.department_model import DepartmentDB
from app.auth.hash_password import hash_password

router = APIRouter(prefix="/employees", tags=["Employees"])



# Create a new employee, link them to the company, link them to a department, link them to a role
# Save everything in DB
@router.post("/", response_model=EmployeeResponse)
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
    departments_details = db.query(DepartmentDB).filter(DepartmentDB.id.in_(employee.dept_id)).all()

    departments = [d.dept_name for d in departments_details]

    if len(departments) != len(employee.dept_id):
        raise HTTPException(
            status_code=404,
            detail="One or more departments not found"
        )

    # Create a new employee
    new_employee = EmployeeDB(**employee.model_dump(exclude={"password"}))
    new_employee.set_password(employee.password)

    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)

    return new_employee




# Get all employees (Fixed Validation Input should be a valid list)
@router.get("/", response_model=List[EmployeeResponse])
def get_employees(db: Session = Depends(get_db)):
    employees = db.query(EmployeeDB).all()
    return employees if employees else []





# Update an employee

@router.put("/{emp_id}", response_model=EmployeeResponse)
def update_employee(emp_id: int, employee_update: EmployeeUpdate, db: Session = Depends(get_db)):
    """Safely executes partial updates on basic details or the JSON department array"""
    db_employee = db.query(EmployeeDB).filter(EmployeeDB.emp_id == emp_id).first()
    if not db_employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Convert schema payload to a dict, discarding unset optional elements
    update_data = employee_update.model_dump(exclude_unset=True)

    # Validate new department allocation if dept_id list is explicitly provided
    if "dept_id" in update_data and update_data["dept_id"]:
        valid_depts = db.query(DepartmentDB).filter(DepartmentDB.id.in_(update_data["dept_id"])).all()
        if len(valid_depts) != len(update_data["dept_id"]):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more departments not found"
            )

    # Set attributes dynamically on database model instance
    for key, value in update_data.items():
        setattr(db_employee, key, value)

    db.commit()
    db.refresh(db_employee)
    return db_employee


# Get an employee by ID (Clean & Lean)
@router.get("/{emp_id}", response_model=EmployeeResponse)
def get_employee_by_id(emp_id: int, db: Session = Depends(get_db)):
    emp = db.query(EmployeeDB).filter(EmployeeDB.emp_id == emp_id).first()

    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee with given ID not found"
        )

    # No manual department queries or mapping needed!
    # Pydantic reads the 'departments' property directly from your model.
    return emp


# Delete an employee
@router.delete("/{emp_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(emp_id: int, db: Session = Depends(get_db)):
    emp = db.query(EmployeeDB).filter(EmployeeDB.emp_id == emp_id).first()

    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee with given ID not found"
        )

    db.delete(emp)
    db.commit()

    # 204 NO CONTENT means successfully deleted, returning no body
    return None