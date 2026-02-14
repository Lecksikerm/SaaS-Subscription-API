import uuid
from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    ABANDONED = "abandoned"

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Relationship to User
    user = relationship("User", back_populates="transactions")
    
    # Paystack fields
    reference = Column(String(255), unique=True, index=True, nullable=False)
    paystack_transaction_id = Column(String(255), nullable=True)
    
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="NGN")
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    
    # Subscription info
    plan_id = Column(String(50), nullable=False)
    payment_channel = Column(String(50), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # Raw response for debugging
    gateway_response = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Transaction {self.reference} - {self.status}>"
