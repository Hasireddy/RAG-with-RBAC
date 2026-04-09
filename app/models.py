from pydantic import BaseModel

class Company(BaseModel):
    id:int
    company_name:str
    domain:str
    location:str
