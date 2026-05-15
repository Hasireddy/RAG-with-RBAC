from pydantic import BaseModel,  ConfigDict
from datetime import datetime
from typing import Dict, Any

class MessageSchema(BaseModel):
    role: str
    message:  Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)