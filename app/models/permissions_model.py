from sqlalchemy import Column, Integer, String, ForeignKey, Table, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.base import Base
from app.models.association import role_permissions

# Create database tables

class PermissionDB(Base):
    """Permissions based on the role of the Employee"""

    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    permission_name = Column(String, unique=True, nullable=False, index=True)

    roles = relationship(
        "RoleDB",
        secondary=role_permissions,
        back_populates="permissions",
        lazy="selectin"
    )