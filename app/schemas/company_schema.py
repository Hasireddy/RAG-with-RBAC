from datetime import datetime
from pydantic import BaseModel, Field

# pydantic models for API validation

class CompanyCreate(BaseModel):
    """Model for creating Company"""

    company_name:str = Field(
        min_length=3,
        max_length=50,
        description="Company name (alphabets only)",
    )
    domain:str
    location:str


class CompanyResponse(BaseModel):
    """Company response model"""

    id: int
    company_name: str
    domain: str
    location: str
    created_at: datetime

    class Config:
        from_attributes = True