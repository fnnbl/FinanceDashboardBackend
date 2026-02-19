from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud import plan as plan_crud
from app.schemas.plan import PlanCreate, PlanUpdate, PlanResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    plan_create: PlanCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await plan_crud.create_plan(db, user_id=current_user.id, plan_create=plan_create)


@router.get("/", response_model=list[PlanResponse])
async def get_plans(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await plan_crud.get_plans_with_stats(db, user_id=current_user.id)


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plan = await plan_crud.get_plan_by_id(db, plan_id=plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    if plan.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this plan")
    plan_with_stats = await plan_crud.get_plan_with_stats(db, plan_id=plan_id)
    return plan_with_stats


@router.put("/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: int,
    plan_update: PlanUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plan = await plan_crud.get_plan_by_id(db, plan_id=plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    if plan.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this plan")
    await plan_crud.update_plan(db, plan=plan, plan_update=plan_update)
    return await plan_crud.get_plan_with_stats(db, plan_id=plan_id)
