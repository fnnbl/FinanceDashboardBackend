from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class PlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class PlanUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None


class PlanResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    budget_item_count: int = 0
    total_monthly_income: float = 0.0
    total_monthly_expenses: float = 0.0
    monthly_balance: float = 0.0

    class Config:
        from_attributes = True
