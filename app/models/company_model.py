from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base


# Create database tables

class CompanyDB(Base):
    """Database model for Company"""

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, index=True, unique=True, nullable=False)
    domain = Column(String, index=True, nullable=False)
    location = Column(String, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship: One Company can have many departments and employees
    departments = relationship("DepartmentDB", back_populates="company")
    employees = relationship("EmployeeDB", back_populates="company")


