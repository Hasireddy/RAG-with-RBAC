from app.database.base import Base
from app.database.session import engine
import app.models  # ensures models are loaded
from sqlalchemy import inspect
from app.models.company_model import CompanyDB


def init_db():
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    print("Tables in DB:", inspector.get_table_names())