from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.budget_item import BudgetItem
from app.schemas.budget_item import BudgetItemCreate


async def get_budget_items_by_plan(db: AsyncSession, plan_id: int) -> list[dict]:
    result = await db.execute(
        select(BudgetItem)
        .where(BudgetItem.plan_id == plan_id)
        .order_by(BudgetItem.type, BudgetItem.created_at)
    )
    items = result.scalars().all()
    return [_item_to_dict(item) for item in items]


async def create_budget_item(db: AsyncSession, plan_id: int, item_create: BudgetItemCreate) -> dict:
    db_item = BudgetItem(
        plan_id=plan_id,
        category_id=item_create.category_id,
        description=item_create.description,
        amount=item_create.amount,
        type=item_create.type,
        payment_rhythm=item_create.payment_rhythm,
        note=item_create.note,
    )
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return _item_to_dict(db_item)


def _item_to_dict(item: BudgetItem) -> dict:
    return {
        "id": item.id,
        "plan_id": item.plan_id,
        "category_id": item.category_id,
        "description": item.description,
        "amount": float(item.amount),
        "type": item.type,
        "payment_rhythm": item.payment_rhythm,
        "monthly_amount": round(float(item.monthly_amount), 2),
        "note": item.note,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }
