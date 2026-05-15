from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from typing import List
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base
from app.auth.hash_password import hash_password, verify_password

# Create database tables

class EmployeeDB(Base):
    """Database model for Employee"""

    __tablename__ = "employees"

    emp_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    emp_name = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    job_title = Column(String, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Foreign key: Each employee belongs to a department and each department belongs to a company
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    dept_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), index=True, nullable=False)


    # Relationship: Employee is in Department and in a Company
    company = relationship("CompanyDB", back_populates="employees")
    department = relationship("DepartmentDB", back_populates="employees")


    # Password Helpers
    def set_password(self, password: str):
        """Hash and store password"""
        self.hashed_password = hash_password(password)

    def check_password(self, password: str) -> bool:
        """Verify password against hash"""
        return verify_password(password, self.hashed_password)
