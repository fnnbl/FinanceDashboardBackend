from fastapi import APIRouter
from app.api.v1.endpoints import auth, plans

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(plans.router, prefix="/plans", tags=["Plans"])
