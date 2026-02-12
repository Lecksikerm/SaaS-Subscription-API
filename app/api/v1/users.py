from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_active_user, get_db, security
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.core.security import get_password_hash

router = APIRouter()

@router.get("/me", response_model=UserResponse)
def read_user_me(current_user: User = Depends(get_current_active_user)):
    """Get current user profile"""
    return current_user

@router.patch("/me", response_model=UserResponse)
def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    
    # Update full_name if provided
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    # Update password if provided
    if user_update.password is not None:
        current_user.password_hash = get_password_hash(user_update.password)
    
    # Update is_verified if provided
    if user_update.is_verified is not None:
        current_user.is_verified = user_update.is_verified
    
    db.commit()
    db.refresh(current_user)
    return current_user
