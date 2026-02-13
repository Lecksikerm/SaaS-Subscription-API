import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_active_user, get_db
from app.core.plans import get_all_plans, get_plan
from app.services.paystack import PaystackService
from app.models.user import User
from app.models.transaction import Transaction, TransactionStatus

router = APIRouter()

SUBSCRIPTION_PERIOD_DAYS = {
    "free": None,  # No expiration
    "basic": 30,
    "pro": 30,
    "enterprise": 30
}

@router.get("/plans")
def list_plans():
    return get_all_plans()

@router.post("/subscribe/{plan_id}")
def subscribe_to_plan(
    plan_id: str, 
    current_user: User = Depends(get_current_active_user), 
    db: Session = Depends(get_db)
):
    """Initialize subscription payment"""
    plan = get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    if plan_id == "free":
        current_user.subscription_tier = plan_id
        current_user.subscription_start_date = None
        current_user.subscription_end_date = None
        db.commit()
        return {"message": "Subscribed to Free plan", "plan": plan}
    
    # Calculate subscription dates
    start_date = datetime.utcnow()
    period_days = SUBSCRIPTION_PERIOD_DAYS.get(plan_id, 30)
    end_date = start_date + timedelta(days=period_days)
    
    # Initialize Paystack payment
    amount_kobo = plan["price"] * 100
    reference = f"sub_{current_user.id}_{uuid.uuid4().hex[:8]}"
    
    # Create pending transaction
    transaction = Transaction(
        user_id=current_user.id,
        reference=reference,
        plan_id=plan_id,
        amount=plan["price"],
        currency="NGN",
        status=TransactionStatus.PENDING
    )
    db.add(transaction)
    db.commit()
    
    result = PaystackService.initialize_transaction(
        email=current_user.email,
        amount=amount_kobo,
        reference=reference,
        callback_url=f"http://localhost:8000/api/v1/subscriptions/verify?reference={reference}",
        metadata={
            "user_id": str(current_user.id), 
            "plan_id": plan_id,
            "reference": reference,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    )
    
    if result.get("status"):
        return {
            "message": "Payment initialized. Complete payment at the URL below.",
            "authorization_url": result["data"]["authorization_url"],
            "reference": reference,
            "plan": plan_id,
            "amount": plan["price"],
            "period_days": period_days,
            "valid_until": end_date.isoformat()
        }
    else:
        transaction.status = TransactionStatus.FAILED
        transaction.gateway_response = result.get("message")
        db.commit()
        raise HTTPException(status_code=400, detail=f"Payment initialization failed: {result.get('message')}")

@router.get("/verify")
def verify_payment(reference: str, db: Session = Depends(get_db)):
    """Verify payment and activate subscription"""
    result = PaystackService.verify_transaction(reference)
    
    if not result.get("status"):
        raise HTTPException(status_code=400, detail="Verification failed")
    
    data = result["data"]
    transaction = db.query(Transaction).filter(Transaction.reference == reference).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if data["status"] != "success":
        transaction.status = TransactionStatus.FAILED
        db.commit()
        return {"message": "Payment not successful", "status": data["status"]}
    
    # Get metadata
    metadata = data.get("metadata", {})
    start_date = datetime.fromisoformat(metadata.get("start_date", datetime.utcnow().isoformat()))
    end_date = datetime.fromisoformat(metadata.get("end_date", (datetime.utcnow() + timedelta(days=30)).isoformat()))
    
    # Update transaction
    transaction.status = TransactionStatus.SUCCESS
    transaction.paystack_transaction_id = str(data.get("id"))
    transaction.payment_channel = data.get("channel")
    transaction.paid_at = data.get("paid_at")
    db.commit()
    
    # Update user subscription with dates
    user = db.query(User).filter(User.id == transaction.user_id).first()
    if user:
        user.subscription_tier = transaction.plan_id
        user.subscription_start_date = start_date
        user.subscription_end_date = end_date
        db.commit()
    
    return {
        "message": "Payment successful! Subscription activated.",
        "plan": transaction.plan_id,
        "valid_from": start_date.isoformat(),
        "valid_until": end_date.isoformat(),
        "status": "active"
    }

@router.get("/status")
def get_subscription_status(current_user: User = Depends(get_current_active_user)):
    """Get current subscription status"""
    is_active = current_user.is_subscription_active()
    
    return {
        "user_id": str(current_user.id),
        "email": current_user.email,
        "subscription_tier": current_user.subscription_tier,
        "is_active": is_active,
        "valid_from": current_user.subscription_start_date.isoformat() if current_user.subscription_start_date else None,
        "valid_until": current_user.subscription_end_date.isoformat() if current_user.subscription_end_date else None,
        "auto_renew": current_user.auto_renew,
        "days_remaining": (
            (current_user.subscription_end_date - datetime.now(current_user.subscription_end_date.tzinfo)).days 
            if current_user.subscription_end_date and current_user.subscription_tier != "free"
            else None
        )
    }

@router.get("/history")
def get_payment_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get payment history"""
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.created_at.desc()).all()
    
    return {
        "user_id": str(current_user.id),
        "subscription_tier": current_user.subscription_tier,
        "transactions": [
            {
                "id": str(t.id),
                "reference": t.reference,
                "amount": float(t.amount),
                "currency": t.currency,
                "status": t.status.value,
                "plan_id": t.plan_id,
                "paid_at": t.paid_at,
                "created_at": t.created_at
            }
            for t in transactions
        ]
    }

@router.post("/cancel")
def cancel_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel auto-renewal (downgrade to free at end of period)"""
    if current_user.subscription_tier == "free":
        raise HTTPException(status_code=400, detail="No active paid subscription")
    
    current_user.auto_renew = False
    db.commit()
    
    return {
        "message": "Auto-renewal cancelled. You will be downgraded to Free at the end of your billing period.",
        "current_plan": current_user.subscription_tier,
        "valid_until": current_user.subscription_end_date.isoformat() if current_user.subscription_end_date else None
    }

@router.post("/test-verify/{reference}")
def test_verify_payment(reference: str, plan_id: str = "basic", db: Session = Depends(get_db)):
    """TEST: Simulate payment"""
    try:
        parts = reference.split("_")
        user_id = parts[1]
    except:
        raise HTTPException(status_code=400, detail="Invalid reference")
    
    transaction = db.query(Transaction).filter(Transaction.reference == reference).first()
    if not transaction:
        transaction = Transaction(
            user_id=user_id,
            reference=reference,
            plan_id=plan_id,
            amount=5000,
            status=TransactionStatus.PENDING
        )
        db.add(transaction)
    
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=30)
    
    transaction.status = TransactionStatus.SUCCESS
    transaction.paid_at = datetime.utcnow().isoformat()
    
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.subscription_tier = plan_id
        user.subscription_start_date = start_date
        user.subscription_end_date = end_date
    
    db.commit()
    
    return {
        "message": "TEST: Payment simulated",
        "plan": plan_id,
        "valid_from": start_date.isoformat(),
        "valid_until": end_date.isoformat(),
        "status": "active"
    }
