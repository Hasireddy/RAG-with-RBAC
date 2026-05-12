from pydantic import BaseModel
from typing import Any


# pydantic model for API validation

class ResponseSchema(BaseModel):
    id: int
    result: Any #str,dict,list

    class Config:
        from_attributes = True


