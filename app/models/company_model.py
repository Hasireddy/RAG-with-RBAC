from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base


# Create database table

class CompanyDB(Base):
    """Database model for Company"""

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True, unique=True, nullable=False)
    domain = Column(String, index=True, nullable=False)
    location = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship: One Company can have many departments and employees
    departments = relationship("DepartmentDB", back_populates="company", cascade="all, delete-orphan")
    employees = relationship("EmployeeDB", back_populates="company", cascade="all, delete-orphan")
    documents = relationship("DocumentDB", back_populates="company", cascade="all, delete-orphan")

