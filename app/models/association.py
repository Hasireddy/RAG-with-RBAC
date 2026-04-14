from sqlalchemy import Table, Column, ForeignKey, UniqueConstraint
from app.database.base import Base


role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), index=True),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), index=True),
    UniqueConstraint("role_id", "permission_id")
)