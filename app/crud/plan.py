from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from typing import Optional

from app.models.plan import Plan
from app.models.budget_item import BudgetItem, BudgetItemType, PaymentRhythm
from app.schemas.plan import PlanCreate


async def create_plan(db: AsyncSession, user_id: int, plan_create: PlanCreate) -> dict:
    db_plan = Plan(
        user_id=user_id,
        name=plan_create.name,
        description=plan_create.description,
    )
    db.add(db_plan)
    await db.commit()
    await db.refresh(db_plan)
    return _plan_to_dict(db_plan, 0, 0.0, 0.0)


async def get_plans_with_stats(db: AsyncSession, user_id: int) -> list[dict]:
    plans = await db.execute(
        select(Plan).where(Plan.user_id == user_id).order_by(Plan.created_at.desc())
    )
    plans = list(plans.scalars().all())

    result = []
    for plan in plans:
        stats = await _get_plan_stats(db, plan.id)
        result.append(_plan_to_dict(plan, *stats))
    return result


async def get_plan_with_stats(db: AsyncSession, plan_id: int) -> Optional[dict]:
    plan_result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = plan_result.scalars().first()
    if not plan:
        return None
    stats = await _get_plan_stats(db, plan.id)
    return _plan_to_dict(plan, *stats)


async def get_plan_by_id(db: AsyncSession, plan_id: int) -> Optional[Plan]:
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    return result.scalars().first()


async def _get_plan_stats(db: AsyncSession, plan_id: int) -> tuple[int, float, float]:
    monthly_amount_expr = case(
        (BudgetItem.payment_rhythm == PaymentRhythm.MONTHLY, BudgetItem.amount),
        (BudgetItem.payment_rhythm == PaymentRhythm.QUARTERLY, BudgetItem.amount / 3),
        (BudgetItem.payment_rhythm == PaymentRhythm.SEMI_ANNUALLY, BudgetItem.amount / 6),
        (BudgetItem.payment_rhythm == PaymentRhythm.ANNUALLY, BudgetItem.amount / 12),
        else_=0,
    )

    result = await db.execute(
        select(
            func.count(BudgetItem.id).label("count"),
            func.coalesce(
                func.sum(case((BudgetItem.type == BudgetItemType.INCOME, monthly_amount_expr), else_=0)), 0
            ).label("income"),
            func.coalesce(
                func.sum(case((BudgetItem.type == BudgetItemType.EXPENSE, monthly_amount_expr), else_=0)), 0
            ).label("expenses"),
        ).where(BudgetItem.plan_id == plan_id)
    )
    row = result.one()
    return int(row.count), float(row.income), float(row.expenses)


def _plan_to_dict(plan: Plan, count: int, income: float, expenses: float) -> dict:
    return {
        "id": plan.id,
        "user_id": plan.user_id,
        "name": plan.name,
        "description": plan.description,
        "created_at": plan.created_at,
        "updated_at": plan.updated_at,
        "budget_item_count": count,
        "total_monthly_income": round(income, 2),
        "total_monthly_expenses": round(expenses, 2),
        "monthly_balance": round(income - expenses, 2),
    }
