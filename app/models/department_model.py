from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship, object_session
from sqlalchemy.sql import func
from app.database.base import Base


# Create database tables

class DepartmentDB(Base):
    """Database model for Department"""

    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    dept_name = Column(String, index=True, nullable=False)
    dept_code = Column(String,
                       index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Foreign key: Each department belongs to the Company
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "dept_code", name="uq_company_dept_code"),
    )

    # Relationship: Departments are in Company and department has employees
    company = relationship("CompanyDB", back_populates="departments",  passive_deletes=True)
    #employees = relationship("EmployeeDB", back_populates="department",  cascade="all, delete-orphan")
    @property
    def employees(self):
        """Dynamically scans Employee JSON lists to find matching team members"""
        session = object_session(self)
        if not session:
            return []

        from app.models.employee_model import EmployeeDB

        # Safe cross-platform filtering for standard SQL JSON arrays
        # Note: If using PostgreSQL, you can use: .filter(EmployeeDB.dept_id.contains([self.id]))
        all_employees = session.query(EmployeeDB).all()
        return [emp for emp in all_employees if emp.dept_id and self.id in emp.dept_id]


