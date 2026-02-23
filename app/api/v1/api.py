from fastapi import APIRouter
from app.api.v1.endpoints import auth, plans, categories, budget_items

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(plans.router, prefix="/plans", tags=["Plans"])
api_router.include_router(categories.router, prefix="/categories", tags=["Categories"])
api_router.include_router(budget_items.router, prefix="/plans/{plan_id}/items", tags=["Budget Items"])
