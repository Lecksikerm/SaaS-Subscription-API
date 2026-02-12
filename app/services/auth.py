from datetime import timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings

class AuthService:
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create_user(db: Session, user_in: UserCreate) -> User:
        db_user = User(
            email=user_in.email,
            password_hash=get_password_hash(user_in.password),
            full_name=user_in.full_name
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        user = AuthService.get_user_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    def login_user(db: Session, user_in: UserLogin) -> Optional[dict]:
        user = AuthService.authenticate_user(db, user_in.email, user_in.password)
        if not user:
            return None
        
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }