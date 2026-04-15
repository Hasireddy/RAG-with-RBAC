from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base


# Create database table

class DocumentDB(Base):
    """Database model for documents"""

    __tablename__ = "documents"


    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    title = Column(String, nullable=False, index=True)

    description = Column(Text, nullable=True)

    file_path = Column(String, nullable=True)  # if uploaded file stored

    content = Column(Text, nullable=True)  # raw text (optional for small docs)

    doc_type = Column(String, default="text")  # pdf, text, url, etc.

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Foreign keys
    company_id = Column(Integer, ForeignKey("companies.id"), index=True, nullable=False)

    dept_id = Column(Integer, ForeignKey("departments.id"), index=True, nullable=False)

    created_by = Column(Integer, ForeignKey("employees.emp_id"), nullable=True)

    # Relationships
    company = relationship("CompanyDB", back_populates="documents")

    department = relationship("DepartmentDB")

    creator = relationship("EmployeeDB")



