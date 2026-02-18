import enum
from decimal import Decimal

from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, Enum, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class BudgetItemType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"


class PaymentRhythm(str, enum.Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUALLY = "semi_annually"
    ANNUALLY = "annually"


class BudgetItem(Base):
    __tablename__ = "budget_items"
    __table_args__ = (
        CheckConstraint("amount > 0", name="check_amount_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    description = Column(String(200), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    type = Column(Enum(BudgetItemType), nullable=False)
    payment_rhythm = Column(Enum(PaymentRhythm), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    plan = relationship("Plan", back_populates="budget_items")
    category = relationship("Category", back_populates="budget_items")

    def calculate_monthly_amount(self) -> Decimal:
        if self.payment_rhythm == PaymentRhythm.MONTHLY:
            return Decimal(self.amount)
        elif self.payment_rhythm == PaymentRhythm.QUARTERLY:
            return Decimal(self.amount) / Decimal(3)
        elif self.payment_rhythm == PaymentRhythm.SEMI_ANNUALLY:
            return Decimal(self.amount) / Decimal(6)
        elif self.payment_rhythm == PaymentRhythm.ANNUALLY:
            return Decimal(self.amount) / Decimal(12)
        return Decimal(0)

    @property
    def monthly_amount(self) -> Decimal:
        return self.calculate_monthly_amount()

    def __repr__(self):
        return f"<BudgetItem(id={self.id}, description='{self.description}', amount={self.amount})>"
