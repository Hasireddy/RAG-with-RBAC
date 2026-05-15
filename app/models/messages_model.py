from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.database.base import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)

    session_id = Column(String, index=True, nullable=False)

    emp_id = Column(String, nullable=True)

    role = Column(String, nullable=False)
    # values:
    # "user"
    # "assistant"
    # "system"

    message = Column(JSON, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )