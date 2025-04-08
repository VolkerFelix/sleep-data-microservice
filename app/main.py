"""Main module for the sleep data microservice.

This module initializes the FastAPI application and includes all necessary
middleware and routes. It serves as the entry point for the microservice.
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import router as api_router
from app.config.settings import settings


# Initialize FastAPI app
def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Sleep Data Microservice",
        description="A microservice for managing and analyzing sleep data",
        version=settings.VERSION,
        docs_url="/docs" if settings.SHOW_DOCS else None,
    )

    app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router)

    @app.get("/")
    async def root():
        """Root endpoint to check if the service is running."""
        return {"message": "Sleep Data Microservice is running"}

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    return app


app = create_application()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
