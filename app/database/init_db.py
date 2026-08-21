from sqlalchemy import inspect, text

from app.database.base import Base
from app.database.session import engine

from app.models.company_model import CompanyDB
from app.models.department_model import DepartmentDB
from app.models.employee_model import EmployeeDB
from app.models.response_model import AIResponseDB
from app.models.messages_model import ChatMessage
from app.models.document_chunk_model import DocumentChunkDB


def init_db():
    with engine.begin() as connection:
        connection.execute(
            text("CREATE EXTENSION IF NOT EXISTS vector")
        )

    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)

    print(
        "TABLES:",
        inspector.get_table_names()
    )