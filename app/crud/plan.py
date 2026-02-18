from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.models.plan import Plan
from app.schemas.plan import PlanCreate


async def create_plan(db: AsyncSession, user_id: int, plan_create: PlanCreate) -> Plan:
    db_plan = Plan(
        user_id=user_id,
        name=plan_create.name,
        description=plan_create.description,
    )
    db.add(db_plan)
    await db.commit()
    await db.refresh(db_plan)
    return db_plan


async def get_plans_by_user(db: AsyncSession, user_id: int) -> list[Plan]:
    result = await db.execute(
        select(Plan).where(Plan.user_id == user_id).order_by(Plan.created_at.desc())
    )
    return list(result.scalars().all())


async def get_plan_by_id(db: AsyncSession, plan_id: int) -> Optional[Plan]:
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    return result.scalars().first()
