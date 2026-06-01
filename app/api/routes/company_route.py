import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError


from app.schemas.company_schema import CompanyCreate, CompanyResponse, CompanyUpdate
from app.database.session import get_db
from app.models.company_model import CompanyDB


router = APIRouter(prefix="/company", tags=["Companies"])


# Create a company
@router.post("/", response_model=CompanyResponse)
def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    """
    Creates a new company record in the database.
    Verifies that the company name does not exist already before
    inserting new record.

    Args:
        company(CompanyCreate): The incoming request payload containing company information.
        db(Session): SQLAlchemy database session

    Returns:
        CompanyResponse: The company object that was created
    """

    company_name = company.name.strip().lower()

    try:
        # Check for duplicates
        existing_company = db.query(CompanyDB).filter(
            CompanyDB.name == company_name
        ).first()

        if existing_company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company already exists"
            )

        # Insert new record
        db_company = CompanyDB(**company.model_dump())
        db.add(db_company)
        db.commit()
        db.refresh(db_company)

        return db_company


    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create a company due to a database constraint violation."
        )

    # catch DB connection crashes
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal server error occurred."
        )



# Get Company details
@router.get("/", response_model=list[CompanyResponse])
def get_company_info(db: Session = Depends(get_db)):
    """
    Retrieves all registered companies from the database.
    """
    companies = db.query(CompanyDB).all()

    if not companies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found. Please create a Company first."
        )

    #return [CompanyResponse.model_validate(company) for company in companies]
    return companies



# Update Company details
@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(company_id:int, company:CompanyUpdate, db: Session = Depends(get_db) ):
    """
    Updates the details of an existing company by its ID
    :param company_id: The unique database identifier of the company to update.
    :param company: The incoming payload containing fields to update.
    :param db: The active database session injected via dependency
    :return: The updated database company record object.
    """

    company_to_update = db.query(CompanyDB).filter(CompanyDB.id == company_id).first()

    if not company_to_update:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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


# delete a company
@router.delete("/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db)):
    """
    Deletes a company from the database with given ID
    """

    company_to_delete = db.query(CompanyDB).filter(CompanyDB.id == company_id).first()

    if not company_to_delete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company with given id not found"
        )

    db.delete(company_to_delete)
    db.commit()
    return {"message": f"Company with id {company_id} deleted successfully"}



