from fastapi import APIRouter
from app.api.sleep_routes import router as sleep_router

# Main API router
router = APIRouter(prefix="/api")

# Include sleep routes
router.include_router(sleep_router)