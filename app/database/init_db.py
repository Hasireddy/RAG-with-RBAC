from app.database.base import Base
from app.database.session import engine
from app.models import CompanyDB, DepartmentDB, EmployeeDB

import app.models  # ensures models are loaded


def init_db():
    Base.metadata.create_all(bind=engine)