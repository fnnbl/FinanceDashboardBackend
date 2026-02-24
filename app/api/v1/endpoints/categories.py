from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.crud import category as category_crud
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.api.deps import get_current_user
from app.models.user import User
from app.models.category import CategoryType

router = APIRouter()


@router.get("/", response_model=list[CategoryResponse])
async def get_categories(
    type: Optional[CategoryType] = Query(None, description="Filter by type: income or expense"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if type:
        return await category_crud.get_categories_by_type(db, category_type=type)
    return await category_crud.get_all_categories(db)


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_create: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await category_crud.get_category_by_name(db, name=category_create.name)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category name already exists")
    return await category_crud.create_category(db, name=category_create.name, category_type=category_create.type)


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    category = await category_crud.get_category_by_id(db, category_id=category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    existing = await category_crud.get_category_by_name(db, name=category_update.name)
    if existing and existing.id != category_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category name already exists")
    return await category_crud.update_category(db, category=category, name=category_update.name)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    reassign_to: Optional[int] = Query(None, description="Category ID to reassign budget items to"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    category = await category_crud.get_category_by_id(db, category_id=category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    if category.is_system:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="System categories cannot be deleted")
    item_count = await category_crud.count_budget_items_by_category(db, category_id=category_id)
    if item_count > 0 and not reassign_to:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category has {item_count} budget item(s). Provide reassign_to parameter or remove items first.",
        )
    if reassign_to:
        target = await category_crud.get_category_by_id(db, category_id=reassign_to)
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reassign target category not found")
    await category_crud.delete_category(db, category=category, reassign_to_id=reassign_to)
