from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.crud import category as category_crud
from app.schemas.category import CategoryResponse
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
