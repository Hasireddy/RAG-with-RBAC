from pydantic import BaseModel
from datetime import datetime

class MessageSchema(BaseModel):
    role: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True