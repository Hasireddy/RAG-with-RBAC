from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.department_schema import DepartmentCreate, DepartmentResponse, DepartmentUpdate
from app.database.session import get_db
from app.models.department_model import DepartmentDB

router = APIRouter()

# Create a Department
@router.post("/department", response_model=DepartmentResponse)
def create_department(department: DepartmentCreate, db: Session = Depends(get_db)):
    """Create new Department"""

    db_department = DepartmentDB(dept_name=department.dept_name, dept_code = department.dept_code)
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return DepartmentResponse.model_validate(db_department)


# Get all departments
@router.get("/department", response_model=DepartmentResponse)
def get_all_departments(skip: int = 0, limit: int = 10, db:Session=Depends(get_db)):
    """Get all available Departments"""

    departments = db.query(DepartmentDB).offset(skip).limit(limit).all()

    if not departments:
        raise HTTPException(
            status_code=404,
            detail="Company not found. Please create a Company first."
        )

    return DepartmentResponse.model_validate(departments)




# Update a department
@router.put("/department/{dept_id}", response_model=DepartmentResponse)
def update_department(dept_id: int, department: DepartmentUpdate, db: Session = Depends(get_db) ):
    """Update a department based on given id"""

    department_to_update = db.query(DepartmentDB).filter(DepartmentDB.dept_id == dept_id).first()

    if department_to_update is None:
        raise HTTPException(status_code=404, detail="Department with given id not found")

    if department_to_update is None:
        department_to_update.dept_name = department.dept_name

    db.commit()
    db.refresh(department_to_update)
    return department_to_update


# Delete a department
@router.delete("/department/{dept_id}", response_model=DepartmentResponse)
def delete_department(dept_id: int, db: Session = Depends(get_db)):
    """Deletes a department by given id"""

    department_to_delete = db.query(DepartmentDB).filter(DepartmentDB.dept_id == dept_id).first()

    if department_to_delete is None:
        raise HTTPException(status_code=404, detail="Department with given id not found")

    db.delete(department_to_delete)
    db.commit()
    return f"Department with id {dept_id} deleted successfully"



# Get departments by department id
@router.get("/department/{dept_id}", response_model=DepartmentResponse)
def get_single_department_by_id(dept_id: int, db: Session = Depends(get_db)):
    """Get department by id"""

    department = db.query(DepartmentDB).filter(DepartmentDB.id == dept_id).first()

    if department is None:
        raise HTTPException(status_code=404, detail = "Department with given id not found")
    return department


