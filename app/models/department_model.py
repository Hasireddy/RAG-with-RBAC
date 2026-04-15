from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base


# Create database tables

class DepartmentDB(Base):
    """Database model for Department"""

    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    dept_name = Column(String, index=True, nullable=False)
    dept_code = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Foreign key: Each department belongs to the Company
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "dept_code", name="uq_company_dept_code"),
    )

    # Relationship: Departments are in Company and department has employees
    company = relationship("CompanyDB", back_populates="departments",  passive_deletes=True)
    employees = relationship("EmployeeDB", back_populates="department",  cascade="all, delete-orphan")


