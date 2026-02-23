from pydantic import BaseModel
from datetime import datetime


class CategoryResponse(BaseModel):
    id: int
    name: str
    type: str
    is_system: bool
    created_at: datetime

    class Config:
        from_attributes = True
