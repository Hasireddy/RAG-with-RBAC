from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base

# Create database tables

class EmployeeDB(Base):
    """Database model for Employee"""

    __tablename__ = "employees"

    emp_id = Column(Integer, primary_key=True, index=True)
    emp_name = Column(String, index=True, nullable=False)
    job_title = Column(String, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Foreign key: Each employee belongs to a department and each department belongs to a company
    dept_id = Column(Integer, ForeignKey("departments.dept_id", ondelete="CASCADE"))
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    role_id = Column(Integer, ForeignKey("roles.id"))

    # Relationship: Employee is in Department and in a Company
    department = relationship("DepartmentDB", back_populates="employees")
    company = relationship("CompanyDB", back_populates="employees")
    role = relationship("RoleDB", back_populates="employees")

