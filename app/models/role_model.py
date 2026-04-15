from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.base import Base
from app.models.association import role_permissions

# Create database tables

class RoleDB(Base):
    """Role of employee in each department
    like CEO, Manager, Employee, HR, Finance, Admin etc"""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String, unique=True, nullable=False, index=True)

    employees = relationship("EmployeeDB", back_populates="role",  passive_deletes=True)

    permissions = relationship(
        "PermissionDB",
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin"
    )
