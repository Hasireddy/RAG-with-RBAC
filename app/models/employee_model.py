from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base

# Create database tables

class EmployeeDB(Base):
    """Database model for Employee"""

    __tablename__ = "employees"

    emp_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    emp_name = Column(String, index=True, nullable=False)
    job_title = Column(String, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Foreign key: Each employee belongs to a department and each department belongs to a company
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    dept_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), index=True, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), index=True, nullable=False)

    # Relationship: Employee is in Department and in a Company

    company = relationship("CompanyDB", back_populates="employees")
    department = relationship("DepartmentDB", back_populates="employees")
    role = relationship("RoleDB", back_populates="employees")

