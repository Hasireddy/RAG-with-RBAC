from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.schemas.employee_schema import EmployeeCreate, EmployeeResponse, EmployeeUpdate
from app.database.session import get_db
from app.models.employee_model import EmployeeDB
from app.models.company_model import CompanyDB
from app.models.department_model import DepartmentDB
from app.auth.hash_password import hash_password

router = APIRouter(prefix="/employees", tags=["Employees"])

# Get all employees
@router.get("/", response_model=List[EmployeeResponse])
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
    departments = db.query(DepartmentDB).filter(DepartmentDB.id.in_(employee.dept_id)).all()

    if len(departments) != len(employee.dept_id):
        raise HTTPException(
            status_code=404,
            detail="One or more departments not found"
        )


    # Create a new employee
    new_employee = EmployeeDB(
        emp_name=employee.emp_name,
        email=employee.email,
        hashed_password=hash_password(employee.password),
        job_title=employee.job_title,
        company_id=employee.company_id,
        dept_id=employee.dept_id
    )

    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)

    # 5. Fetch department names for response
    departments = db.query(DepartmentDB).filter(
        DepartmentDB.id.in_(new_employee.dept_id)
    ).all()

    dept_list = [
        {
            "id": d.id,
            "dept_name": d.dept_name
        }
        for d in departments
    ]

    # 6. Return structured response
    return EmployeeResponse(
        emp_id=new_employee.emp_id,
        emp_name=new_employee.emp_name,
        job_title=new_employee.job_title,
        email=new_employee.email,
        dept_id=new_employee.dept_id,
        departments=dept_list,
        company_id=new_employee.company_id,
        is_active=new_employee.is_active,
        created_at=new_employee.created_at
    )



# Update an employee
@router.put("/{emp_id}", response_model=EmployeeResponse)
def update_employee(emp_id: int, employee: EmployeeUpdate, db: Session = Depends(get_db)):

    emp_to_update = db.query(EmployeeDB).filter(
        EmployeeDB.emp_id == emp_id
    ).first()

    if not emp_to_update:
        raise HTTPException(
            status_code=404,
            detail="Employee with given id not found"
        )

    data = employee.model_dump(exclude_unset=True)

    # 3. Validate company if provided
    if "company_id" in data:
        company = db.query(CompanyDB).filter(
            CompanyDB.id == data["company_id"]
        ).first()

        if not company:
            raise HTTPException(
                status_code=404,
                detail="Company not found"
            )

    # 4. Validate departments if provided
    if "dept_id" in data and data["dept_id"] is not None:

        departments = db.query(DepartmentDB).filter(
            DepartmentDB.id.in_(data["dept_id"])
        ).all()

        if len(departments) != len(set(data["dept_id"])):
            raise HTTPException(
                status_code=404,
                detail="One or more departments not found"
            )

    # 5. Apply updates safely
    for field, value in data.items():
        setattr(emp_to_update, field, value)

    db.commit()
    db.refresh(emp_to_update)

    # 6. Build department response (IMPORTANT)
    departments = db.query(DepartmentDB).filter(
        DepartmentDB.id.in_(emp_to_update.dept_id)
    ).all()

    dept_list = [
        {
            "id": d.id,
            "dept_name": d.dept_name
        }
        for d in departments
    ]

    # 7. Return structured response
    return EmployeeResponse(
        emp_id=emp_to_update.emp_id,
        emp_name=emp_to_update.emp_name,
        job_title=emp_to_update.job_title,
        email=emp_to_update.email,
        dept_id=emp_to_update.dept_id,
        departments=dept_list,
        company_id=emp_to_update.company_id,
        is_active=emp_to_update.is_active,
        created_at=emp_to_update.created_at
    )




# Delete an employee
@router.delete("/{emp_id}")
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
@router.get("/", response_model=List[EmployeeResponse])
def get_employees(db: Session = Depends(get_db)):

    employees = db.query(EmployeeDB).all()

    result = []

    for emp in employees:

        departments = db.query(DepartmentDB).filter(
            DepartmentDB.id.in_(emp.dept_id or [])
        ).all()

        dept_list = [
            {
                "id": d.id,
                "dept_name": d.dept_name
            }
            for d in departments
        ]

        result.append(
            EmployeeResponse(
                emp_id=emp.emp_id,
                emp_name=emp.emp_name,
                job_title=emp.job_title,
                email=emp.email,
                dept_id=emp.dept_id,
                departments=dept_list,
                company_id=emp.company_id,
                is_active=emp.is_active,
                created_at=emp.created_at
            )
        )

    return result



@router.get("/employee/{emp_id}", response_model=EmployeeResponse)
def get_employee_by_id(emp_id: int, db: Session = Depends(get_db)):

    emp = db.query(EmployeeDB).filter(
        EmployeeDB.emp_id == emp_id
    ).first()

    if not emp:
        raise HTTPException(
            status_code=404,
            detail="Employee with given id not found"
        )

    departments = db.query(DepartmentDB).filter(
        DepartmentDB.id.in_(emp.dept_id or [])
    ).all()

    dept_list = [
        {
            "id": d.id,
            "dept_name": d.dept_name
        }
        for d in departments
    ]

    return EmployeeResponse(
        emp_id=emp.emp_id,
        emp_name=emp.emp_name,
        job_title=emp.job_title,
        email=emp.email,
        dept_id=emp.dept_id,
        departments=dept_list,
        company_id=emp.company_id,
        is_active=emp.is_active,
        created_at=emp.created_at
    )

