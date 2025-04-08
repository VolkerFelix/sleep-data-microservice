"""API routes module for the sleep data microservice.

This module defines the main API router and includes
all sub-routers for different API endpoints.
It serves as the central point for organizing all API routes.
"""
from fastapi import APIRouter

from app.api.sleep_routes import router as sleep_router

# Main API router
router = APIRouter(prefix="/api")

# Include sleep routes
router.include_router(sleep_router)
