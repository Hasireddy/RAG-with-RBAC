from pydantic import BaseModel, Field
from app.schemas.messages_schema import  MessageSchema


# pydantic model for API validation

class ResponseSchema(BaseModel):
    session_id: str
    messages: list[MessageSchema] = Field(default_factory=list)

    class Config:
        from_attributes = True


