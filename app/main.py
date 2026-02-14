from fastapi import FastAPI
from app.core.config import settings
from app.api.v1 import api_router

def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="SaaS Subscription API with billing and payments",
        version="0.1.0"
    )

    @app.get("/")
    def root():
        return {
            "message": "Welcome to SaaS Subscription API",
            "docs": "/docs",
            "health": "/health"
        }

    @app.get("/health")
    def health_check():
        return {"status": "healthy", "app": settings.app_name}

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")

    return app

app = create_application()
