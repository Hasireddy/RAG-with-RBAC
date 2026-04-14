from fastapi import FastAPI, HTTPException, Depends, Response, status
from dotenv import load_dotenv
import uvicorn
import os

from sqlalchemy.orm import Session

from app.models import *
from app.database import engine, get_db, SessionLocal
from app.database_models import CompanyDB, DepartmentDB, EmployeeDB, Base


app = FastAPI(
    title="RAG with Role Based Access Control",
    description="A private chatbot for a company",
  )

# Create all tables in the database
Base.metadata.create_all(bind=engine)

load_dotenv()  # Loads .env contents into environment

api_key = os.getenv("API_KEY")

"""company = Company(id = 1, company_name =  "Global solutions GMBH", domain =  "www.global.com", location = "Berlin")

departments = [{"dept_id": 1, "dept_name": "Engineering"},
               {"dept_id": 2, "dept_name": "Finance"},
               {"dept_id": 3, "dept_name": "Marketing"},
               ]"""

@app.get("/")
def root():
    return {"Hello": "World"}

# Create Company
@app.post("/company", response_model=CompanyResponse)
def create_company(company:CompanyCreate, db:Session=Depends(get_db)):
    """Create a Company"""

    # Check if a company already exists
    existing_company = db.query(CompanyDB).first()
    if existing_company:
        raise HTTPException(
            status_code=400,
            detail="Company already exists. This system supports only one company."
        )

    #Create a Company if none exists
    db_company = CompanyDB(company_name=company.company_name, domain=company.domain, location=company.location)
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company


# Get Company details
@app.get("/company", response_model=CompanyResponse)
def get_company_info(db:Session=Depends(get_db)):
    company = db.query(CompanyDB).first()

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found. Please create a Company first."
        )

    return CompanyResponse.model_validate(company)



# Update Company details
@app.put("/company")
def update_company():
    pass


# Create a Department
@app.post("/department", response_model=DepartmentResponse)
def create_department(department: DepartmentCreate, db: Session = Depends(get_db)):
    """Create new Department"""

    db_department = DepartmentDB(dept_name=department.dept_name, dept_code = department.dept_code)
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return DepartmentResponse.model_validate(db_department)


# Get all departments
@app.get("/department", response_model=DepartmentResponse)
def get_all_departments(skip: int = 0, limit: int = 10, db:Session=Depends(get_db)):
    departments = db.query(DepartmentDB).offset(skip).limit(limit).all()

    if not departments:
        raise HTTPException(
            status_code=404,
            detail="Company not found. Please create a Company first."
        )

    return DepartmentResponse.model_validate(departments)




# Update a department
@app.put("/department/{dept_id}", response_model=DepartmentResponse)
def update_department(dept_id: int, department: DepartmentUpdate, db: Session = Depends(get_db) ):
    department_to_update = db.query(DepartmentDB).filter(DepartmentDB.dept_id == dept_id).first()

    if department_to_update is None:
        raise HTTPException(status_code=404, detail="Department with given id not found")

    if department_to_update is None:
        department_to_update.dept_name = department.dept_name

    db.commit()
    db.refresh(department_to_update)
    return department_to_update


# Delete a department
@app.delete("/department/{dept_id}", response_model=DepartmentResponse)
def delete_department(dept_id: int, db: Session = Depends(get_db)):
    department_to_delete = db.query(DepartmentDB).filter(DepartmentDB.dept_id == dept_id).first()

    if department_to_delete is None:
        raise HTTPException(status_code=404, detail="Department with given id not found")

    db.delete(department_to_delete)
    db.commit()
    return f"Department with id {dept_id} deleted successfully"



# Sort departments by department name
@app.get("/department/{dept_id}", response_model=DepartmentResponse)
def get_single_department_by_id(dept_id: int, db: Session = Depends(get_db)):
    department = db.query(DepartmentDB).filter(DepartmentDB.id == dept_id).first()

    if department is None:
        raise HTTPException(status_code=404, detail = "Department with given id not found")
    return department




# Get all employees
@app.get("/employees")
def get_employees():
    pass

# Create an employee
@app.post("/employees")
def add_employee():
    pass


# Update an employee
@app.put("/employees")
def update_employee():
    pass


# Delete an employee
@app.delete("/employees")
def delete_employee():
    pass


# Get employee by id
@app.get("/employee/id")
def get_employee_by_id():
    pass


# Get employees by department
@app.get("/employees/dept")
def get_employees_by_department():
    pass




if __name__ == "__main__":
    uvicorn.run(  "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )