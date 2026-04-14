from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator

# Engine: Connect to DB
# Session: Open connection where we interact with DB
# Base: Base class models for creating SQLAlchemy ORM
# Model: Python Class -> DB Table

db_url = "sqlite:///./company_database.db"

engine = create_engine(db_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    """
    Dependency that provides a database session.

    Yields a database session and ensures it's properly closed
    after the request is complete.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
