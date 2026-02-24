from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from sqlalchemy.orm import selectinload

from app.models.budget_item import BudgetItem
from app.models.category import Category
from app.schemas.budget_item import BudgetItemCreate, BudgetItemUpdate


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


async def get_budget_item_by_id(db: AsyncSession, item_id: int) -> BudgetItem | None:
    result = await db.execute(select(BudgetItem).where(BudgetItem.id == item_id))
    return result.scalars().first()


async def update_budget_item(db: AsyncSession, item: BudgetItem, item_update: BudgetItemUpdate) -> dict:
    update_data = item_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item)
    return _item_to_dict(item)


async def get_budget_items_with_category(db: AsyncSession, plan_id: int) -> list[dict]:
    result = await db.execute(
        select(BudgetItem)
        .options(selectinload(BudgetItem.category))
        .where(BudgetItem.plan_id == plan_id)
        .order_by(BudgetItem.type, BudgetItem.created_at)
    )
    items = result.scalars().all()
    result_list = []
    for item in items:
        d = _item_to_dict(item)
        d["category_name"] = item.category.name if item.category else "Unbekannt"
        result_list.append(d)
    return result_list


async def delete_budget_item(db: AsyncSession, item: BudgetItem) -> None:
    await db.delete(item)
    await db.commit()


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
