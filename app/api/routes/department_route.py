from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session


from app.schemas.department_schema import DepartmentCreate, DepartmentResponse, DepartmentUpdate
from app.database.session import get_db
from app.models.company_model import CompanyDB
from app.models.department_model import DepartmentDB

router = APIRouter()

# Create a Department
@router.post("/department", response_model=DepartmentResponse)
def create_department(department: DepartmentCreate, db: Session = Depends(get_db)):
    """Create new Department"""
    company = db.query(CompanyDB).first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Check duplicate dept_code
    existing_dept = db.query(DepartmentDB).filter(DepartmentDB.dept_code == department.dept_code).first()

    if existing_dept:
        raise HTTPException(
            status_code=400,
            detail=f"Department code '{department.dept_code}' already exists"
        )

    db_department = DepartmentDB(
        dept_name=department.dept_name,
        dept_code=department.dept_code,
        company_id=company.id
    )
    db.add(db_department)
    db.commit()
    db.refresh(db_department)

    return db_department


# Get all departments
@router.get("/department", response_model=list[DepartmentResponse])
def get_all_departments(skip: int = 0, limit: int = 10, db:Session=Depends(get_db)):
    """Get all available Departments"""

    departments = db.query(DepartmentDB).offset(skip).limit(limit).all()

    if not departments:
        raise HTTPException(
            status_code=404,
            detail="Departments not found. Please create a department first."
        )

    return departments



# Update a department
@router.put("/department/{dept_id}", response_model=DepartmentResponse)
def update_department(dept_id: int, department: DepartmentUpdate, db: Session = Depends(get_db) ):
    """Update a department based on given id"""

    department_to_update = db.query(DepartmentDB).filter(DepartmentDB.id == dept_id).first()

    if not department_to_update:
        raise HTTPException(status_code=404, detail="Department with given id not found")

    if department.dept_name is not None:
        department_to_update.dept_name = department.dept_name

    if department.dept_code is not None:
        department_to_update.dept_code = department.dept_code

    db.commit()
    db.refresh(department_to_update)
    return department_to_update


# Delete a department
@router.delete("/department/{dept_id}")
def delete_department(dept_id: int, db: Session = Depends(get_db)):
    """Deletes a department by given id"""

    department_to_delete = db.query(DepartmentDB).filter(DepartmentDB.id == dept_id).first()

    if not department_to_delete:
        raise HTTPException(status_code=404, detail="Department with given id not found")

    db.delete(department_to_delete)
    db.commit()
    return {"message": f"Department {dept_id} deleted successfully"}



# Get departments by department id
@router.get("/department/{dept_id}", response_model=DepartmentResponse)
def get_single_department_by_id(dept_id: int, db: Session = Depends(get_db)):
    """Get department by id"""

    department = db.query(DepartmentDB).filter(DepartmentDB.id == dept_id).first()

    if not department:
        raise HTTPException(status_code=404, detail = "Department with given id not found")
    return department


