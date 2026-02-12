from fastapi import FastAPI
from sqlalchemy import text
from app.core.config import settings
from app.db.session import engine
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

    @app.on_event("startup")
    async def test_db():
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                conn.commit()
            print("✅ Database connected successfully on port 5434")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise e

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")

    return app

app = create_application()
