from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import traceback

from app.schemas.company_schema import CompanyCreate, CompanyResponse, CompanyUpdate
from app.database.session import get_db
from app.models.company_model import CompanyDB

router = APIRouter()

# Create a company
@router.post("/company", response_model=CompanyResponse)
def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    try:
        existing_company = db.query(CompanyDB).filter(
            CompanyDB.name == company.name.strip().lower()
        ).first()

        if existing_company:
            raise HTTPException(status_code=400, detail="Company already exists")

        db_company = CompanyDB(**company.model_dump())
        db.add(db_company)
        db.commit()
        db.refresh(db_company)

        return db_company

    except IntegrityError as e:
        db.rollback()
        print(traceback.format_exc())  # 👈 IMPORTANT
        raise HTTPException(status_code=400, detail=str(e))



# Get Company details
@router.get("/company", response_model=list[CompanyResponse])
def get_company_info(db: Session = Depends(get_db)):
    companies = db.query(CompanyDB).all()

    if not companies:
        raise HTTPException(
            status_code=404,
            detail="Company not found. Please create a Company first."
        )

    #return [CompanyResponse.model_validate(company) for company in companies]
    return companies


# Update Company details
@router.put("/company/{company_id}", response_model=CompanyResponse)
def update_company(company_id:int, company:CompanyUpdate, db: Session = Depends(get_db) ):
    company_to_update = db.query(CompanyDB).filter(CompanyDB.id == company_id).first()

    if not company_to_update:
        raise HTTPException(
            status_code=404,
            detail="Company not found with given id"
        )

    if company.name is not None:
        company_to_update.name = company.name

    if company.domain is not None:
        company_to_update.domain = company.domain

    if company.location is not None:
        company_to_update.location = company.location

    if company.is_active is not None:
        company_to_update.is_active = company.is_active

    db.commit()
    db.refresh(company_to_update)

    return company_to_update


@router.delete("/company/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db)):
    company_to_delete = db.query(CompanyDB).filter(CompanyDB.id == company_id).first()

    if not company_to_delete:
        raise HTTPException(
            status_code=400,
            detail="Company with given id not found"
        )

    db.delete(company_to_delete)
    db.commit()
    return {"message": f"Company with id {company_id} deleted successfully"}



