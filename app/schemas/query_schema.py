from pydantic import BaseModel

# user query request
class QueryRequest(BaseModel):
    query: str
    user_id: str



# Response from the system
class ResponseSchema(BaseModel):
    id: int
    result: str