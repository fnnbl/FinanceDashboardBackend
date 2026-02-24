from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

from app.models.budget_item import BudgetItemType, PaymentRhythm


class BudgetItemCreate(BaseModel):
    category_id: int
    description: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0)
    type: BudgetItemType
    payment_rhythm: PaymentRhythm
    note: Optional[str] = None


class BudgetItemUpdate(BaseModel):
    category_id: Optional[int] = None
    description: Optional[str] = Field(None, min_length=1, max_length=200)
    amount: Optional[float] = Field(None, gt=0)
    type: Optional[BudgetItemType] = None
    payment_rhythm: Optional[PaymentRhythm] = None
    note: Optional[str] = None


class BudgetItemResponse(BaseModel):
    id: int
    plan_id: int
    category_id: int
    description: str
    amount: float
    type: BudgetItemType
    payment_rhythm: PaymentRhythm
    monthly_amount: float
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
