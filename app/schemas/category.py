from pydantic import BaseModel, Field
from datetime import datetime

from app.models.category import CategoryType


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: CategoryType


class CategoryUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class CategoryResponse(BaseModel):
    id: int
    name: str
    type: str
    is_system: bool
    created_at: datetime

    class Config:
        from_attributes = True
