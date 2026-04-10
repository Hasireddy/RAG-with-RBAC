from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

Base = declarative_base()

# Create database tables
class CompanyDB(Base):
    """Database model for Company"""

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, index=True, nullable=False)
    domain = Column(String, index=True, nullable=False)
    location = Column(String, index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship: One Company can have many departments and employees
    departments = relationship("DepartmentDB", back_populates="company")
    employees = relationship("EmployeeDB", back_populates="company")


class DepartmentDB(Base):
    """Database model for Department"""

    __tablename__ = "departments"

    dept_id = Column(Integer, primary_key=True, index=True)
    dept_name = Column(String, index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    company_id = Column(Integer, ForeignKey("companies.id"))

    # Relationship: Departments are in Company and department has employees
    company = relationship("CompanyDB", back_populates="departments")
    employees = relationship("EmployeeDB", back_populates="department")




class EmployeeDB(Base):
    """Database model for Employee"""

    __tablename__ = "employees"

    emp_id = Column(Integer, primary_key=True, index=True)
    emp_name = Column(String, index=True, nullable=False)
    job_title = Column(String, index=True, nullable=False)
    manager_id = Column(Integer, nullable=True)

    dept_id = Column(Integer, ForeignKey("departments.dept_id"))
    company_id = Column(Integer, ForeignKey("companies.id"))

    # Relationship: Employee is in Department and in a Company
    department = relationship("DepartmentDB", back_populates="employees")
    company = relationship("CompanyDB", back_populates="employees")