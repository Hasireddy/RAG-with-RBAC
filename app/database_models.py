from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

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



class DepartmentDB(Base):
    """Database model for Department"""

    __tablename__ = "departments"

    dept_id = Column(Integer, primary_key=True, index=True)
    dept_name = Column(String, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Foreign key: Each department belongs to the Company
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))

    # Relationship: Departments are in Company and department has employees
    company = relationship("CompanyDB", back_populates="departments")
    employees = relationship("EmployeeDB", back_populates="department",  cascade="all, delete")




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




role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), index=True),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), index=True),
    UniqueConstraint("role_id", "permission_id")
)


class RoleDB(Base):
    """Role of employee in each department
    like CEO, Manager, Employee, HR, Finance, Admin etc"""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    role_name = Column(String, unique=True, nullable=False, index=True)

    employees = relationship("EmployeeDB", back_populates="role")

    permissions = relationship(
        "PermissionDB",
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin"
    )


class PermissionDB(Base):
    """Permissions based on the role of the Employee"""

    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True)
    permission_name = Column(String, unique=True, nullable=False, index=True)

    roles = relationship(
        "RoleDB",
        secondary=role_permissions,
        back_populates="permissions",
        lazy="selectin"
    )