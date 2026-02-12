import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import enum
from app.db.base import Base

class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # Subscription fields
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    
    # Stripe/Paystack customer ID
    payment_customer_id = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<User {self.email}>"