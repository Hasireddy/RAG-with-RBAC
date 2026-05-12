from pydantic import BaseModel
from typing import Optional

# user query request
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None




# Response from the system
class ResponseSchema(BaseModel):
    id: int
    result: str