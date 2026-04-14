from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.company_schema import CompanyCreate, CompanyResponse
from app.database.session import get_db
from app.models.company_model import CompanyDB

router = APIRouter()

# Create a company
@router.post("/company", response_model=CompanyResponse)
def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    existing_company = db.query(CompanyDB).first()

    if existing_company:
        raise HTTPException(status_code=400, detail="Company already exists")

    db_company = CompanyDB(**company.model_dump())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)

    return db_company



# Get Company details
@router.get("/company", response_model=CompanyResponse)
def get_company_info(db:Session=Depends(get_db)):
    company = db.query(CompanyDB).first()

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found. Please create a Company first."
        )

    return CompanyResponse.model_validate(company)


# Update Company details
@router.put("/company")
def update_company():
    pass

