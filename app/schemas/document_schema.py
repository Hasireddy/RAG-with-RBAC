from pydantic import BaseModel, Field
from typing import Optional

# pydantic model for API validation

class DocumentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    description: Optional[str] = None
    content: Optional[str] = None
    doc_type: str = Field(default="text")
