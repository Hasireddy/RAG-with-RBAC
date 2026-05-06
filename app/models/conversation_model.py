from sqlalchemy import Column, Integer, String, Text
from app.database.base import Base

# Create database table for all the conversations including queries

class ConversationDB(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(String, index=True)

    query = Column(Text, nullable=False)

    response = Column(Text, nullable=False)