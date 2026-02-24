from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud import plan as plan_crud
from app.crud import budget_item as budget_item_crud
from app.schemas.budget_item import BudgetItemCreate, BudgetItemUpdate, BudgetItemResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


async def _get_plan_or_403(plan_id: int, current_user: User, db: AsyncSession):
    plan = await plan_crud.get_plan_by_id(db, plan_id=plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    if plan.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this plan")
    return plan


@router.get("/", response_model=list[BudgetItemResponse])
async def get_budget_items(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_plan_or_403(plan_id, current_user, db)
    return await budget_item_crud.get_budget_items_by_plan(db, plan_id=plan_id)


@router.post("/", response_model=BudgetItemResponse, status_code=status.HTTP_201_CREATED)
async def create_budget_item(
    plan_id: int,
    item_create: BudgetItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_plan_or_403(plan_id, current_user, db)
    return await budget_item_crud.create_budget_item(db, plan_id=plan_id, item_create=item_create)


@router.put("/{item_id}", response_model=BudgetItemResponse)
async def update_budget_item(
    plan_id: int,
    item_id: int,
    item_update: BudgetItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_plan_or_403(plan_id, current_user, db)
    item = await budget_item_crud.get_budget_item_by_id(db, item_id=item_id)
    if not item or item.plan_id != plan_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget item not found")
    return await budget_item_crud.update_budget_item(db, item=item, item_update=item_update)
