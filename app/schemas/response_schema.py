from pydantic import BaseModel


# pydantic model for API validation

class ResponseSchema(BaseModel):
    id: int
    result: str

    class Config:
        from_attributes = True