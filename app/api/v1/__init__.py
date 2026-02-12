from fastapi import APIRouter
from app.api.v1 import auth, users

api_router = APIRouter()

# Auth routes (public)
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# User routes (protected)
api_router.include_router(users.router, prefix="/users", tags=["users"])
