from sqlalchemy import Column, Integer, Text
from app.database.base import Base


# Create database table

class AIResponseDB(Base):
    """Database model for OpenAI responses"""

    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    result = Column(Text, nullable=False)




