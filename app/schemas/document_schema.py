from pydantic import BaseModel, Field
from typing import Optional, Literal

# pydantic model for API validation

class DocumentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=100, strip_whitespace=True)
    description: Optional[str] = None
    content: Optional[str] = None
    doc_type: Literal["text", "pdf", "csv", "md"] = "text"

    model_config = {
        "str_strip_whitespace": True,
        "extra": "forbid"
    }
