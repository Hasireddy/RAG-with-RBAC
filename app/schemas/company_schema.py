from datetime import datetime
from pydantic import BaseModel, Field, Field, field_validator
from typing import Optional
import re


# pydantic models for API validation

class CompanyCreate(BaseModel):
    """Schema for creating Company"""

    name:str = Field(
        min_length=3,
        max_length=50,
        description="Company name (alphabets only)",
    )
    domain:str = Field(
        description="Company domain (e.g., example.com)"
    )
    location:str= Field(
        min_length=2,
        max_length=100
    )
    is_active: Optional[bool] = True


  # Validate company_name
    @field_validator("company_name")
    @classmethod
    def validate_name(cls, value):
        if not re.match(r"^[A-Za-z ]+$", value):
            raise ValueError("Company name must contain only alphabets and spaces")
        return value

    # Validate domain
    @field_validator("domain")
    @classmethod
    def validate_domain(cls, value):
        pattern = r"^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$"
        if not re.match(pattern, value):
            raise ValueError("Invalid domain format (e.g., company.com)")
        return value.lower()


class CompanyResponse(BaseModel):
    """Company response model"""

    id: int
    name: str
    domain: str
    location: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True