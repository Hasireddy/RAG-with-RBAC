from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any

class MessageSchema(BaseModel):
    role: str
    message:  Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True