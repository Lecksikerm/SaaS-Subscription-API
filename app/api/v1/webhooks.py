from fastapi import APIRouter, Request, HTTPException, Depends, Header, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.api.deps import get_db
from app.services.paystack import PaystackService
from app.models.transaction import Transaction, TransactionStatus
from app.models.user import User
import json

router = APIRouter()

class PaystackWebhookPayload(BaseModel):
    event: str
    data: Dict[str, Any]

@router.post("/paystack")
async def paystack_webhook(
    payload: PaystackWebhookPayload = Body(...),
    x_paystack_signature: str = Header(None),
    db: Session = Depends(get_db)
):
    """Handle Paystack webhooks for automatic payment verification"""
    
    # Convert payload to dict for processing
    payload_dict = payload.dict()
    event = payload_dict.get("event")
    data = payload_dict.get("data", {})
    
    # Handle charge.success event
    if event == "charge.success":
        return await _handle_charge_success(data, db)
    
    # Handle subscription.create event
    elif event == "subscription.create":
        return await _handle_subscription_created(data, db)
    
    # Handle invoice.payment_failed event
    elif event == "invoice.payment_failed":
        return await _handle_payment_failed(data, db)
    
    # Acknowledge other events
    return {"status": "ignored", "event": event}

async def _handle_charge_success(data: dict, db: Session):
    """Process successful payment"""
    reference = data.get("reference")
    metadata = data.get("metadata", {})
    
    if not reference:
        return {"status": "error", "message": "No reference in webhook data"}
    
    # Find transaction
    transaction = db.query(Transaction).filter(
        Transaction.reference == reference
    ).first()
    
    if not transaction:
        # Create transaction if not exists
        user_id = metadata.get("user_id")
        plan_id = metadata.get("plan_id")
        
        if not user_id:
            return {"status": "error", "message": "No user_id in metadata"}
        
        transaction = Transaction(
            user_id=user_id,
            reference=reference,
            plan_id=plan_id or "unknown",
            amount=data.get("amount", 0) / 100,
            currency=data.get("currency", "NGN"),
            status=TransactionStatus.PENDING
        )
        db.add(transaction)
    
    # Update transaction
    transaction.status = TransactionStatus.SUCCESS
    transaction.paystack_transaction_id = str(data.get("id"))
    transaction.payment_channel = data.get("channel")
    transaction.paid_at = data.get("paid_at")
    transaction.gateway_response = data.get("gateway_response")
    
    # Update user subscription
    user = db.query(User).filter(User.id == transaction.user_id).first()
    if user:
        user.subscription_tier = transaction.plan_id
    
    db.commit()
    
    return {
        "status": "success",
        "message": "Payment processed via webhook",
        "reference": reference,
        "user_id": str(transaction.user_id),
        "plan": transaction.plan_id
    }

async def _handle_subscription_created(data: dict, db: Session):
    """Handle new subscription creation"""
    return {"status": "success", "event": "subscription.create"}

async def _handle_payment_failed(data: dict, db: Session):
    """Handle failed renewal payment"""
    customer = data.get("customer", {})
    email = customer.get("email")
    
    # Find user by email
    user = db.query(User).filter(User.email == email).first()
    if user:
        # Could send email notification here
        pass
    
    return {"status": "success", "event": "invoice.payment_failed", "email": email}
