import uuid
import enum
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
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
    
    # Relationship to transactions
    transactions = relationship("Transaction", back_populates="user")
    
    # Subscription fields
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    subscription_start_date = Column(DateTime(timezone=True), nullable=True)
    subscription_end_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    auto_renew = Column(Boolean, default=True)
    
    # Stripe/Paystack customer ID
    payment_customer_id = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    def is_subscription_active(self) -> bool:
        """Check if subscription is currently active"""
        if self.subscription_tier == SubscriptionTier.FREE:
            return True
        if not self.subscription_end_date:
            return False
        return datetime.now(self.subscription_end_date.tzinfo) < self.subscription_end_date

    def __repr__(self):
        return f"<User {self.email} - {self.subscription_tier}>"
