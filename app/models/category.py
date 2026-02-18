import enum

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CategoryType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    type = Column(Enum(CategoryType), nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    budget_items = relationship("BudgetItem", back_populates="category")

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', type='{self.type}')>"
