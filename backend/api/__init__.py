from fastapi import APIRouter
from backend.api import health, receipts, ui
api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(receipts.router, prefix="/api", tags=["receipts"])
api_router.include_router(ui.router, tags=["ui"])
