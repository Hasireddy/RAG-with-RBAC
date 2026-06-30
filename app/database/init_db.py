from app.database.base import Base
from app.database.session import engine
from sqlalchemy import inspect
from app.models.company_model import CompanyDB
from app.models.department_model import DepartmentDB
from app.models.employee_model import EmployeeDB
from app.models.response_model import AIResponseDB
from app.models.messages_model import ChatMessage


def init_db():
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    print("TABLES:", Base.metadata.tables.keys())