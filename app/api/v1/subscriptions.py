import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.api.deps import get_current_active_user, get_db
from app.core.plans import get_all_plans, get_plan
from app.services.paystack import PaystackService
from app.models.user import User
from app.models.transaction import Transaction, TransactionStatus

router = APIRouter()

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
        db.commit()
        return {"message": "Subscribed to Free plan", "plan": plan}
    
    # Initialize Paystack payment
    amount_kobo = plan["price"] * 100
    reference = f"sub_{current_user.id}_{uuid.uuid4().hex[:8]}"
    
    # Create pending transaction record
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
            "reference": reference
        }
    )
    
    if result.get("status"):
        return {
            "message": "Payment initialized. Complete payment at the URL below.",
            "authorization_url": result["data"]["authorization_url"],
            "reference": reference,
            "plan": plan_id,
            "amount": plan["price"]
        }
    else:
        # Mark transaction as failed
        transaction.status = TransactionStatus.FAILED
        transaction.gateway_response = result.get("message")
        db.commit()
        
        raise HTTPException(
            status_code=400, 
            detail=f"Payment initialization failed: {result.get('message')}"
        )

@router.get("/verify")
def verify_payment(
    reference: str, 
    db: Session = Depends(get_db)
):
    """Manual verification (fallback if webhook fails)"""
    result = PaystackService.verify_transaction(reference)
    
    if not result.get("status"):
        raise HTTPException(status_code=400, detail="Verification failed")
    
    data = result["data"]
    
    # Find transaction
    transaction = db.query(Transaction).filter(
        Transaction.reference == reference
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Check if payment was successful
    if data["status"] != "success":
        transaction.status = TransactionStatus.FAILED
        transaction.gateway_response = data.get("gateway_response")
        db.commit()
        
        return {
            "message": "Payment not successful", 
            "status": data["status"],
            "gateway_response": data.get("gateway_response")
        }
    
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
        "message": "Payment successful! Subscription activated.",
        "plan": transaction.plan_id,
        "amount_paid": data["amount"] / 100,
        "currency": data["currency"],
        "status": "active",
        "user_email": user.email if user else None
    }

@router.get("/history")
def get_payment_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's payment history"""
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

@router.post("/test-verify/{reference}")
def test_verify_payment(
    reference: str,
    plan_id: str = "basic",
    db: Session = Depends(get_db)
):
    """TEST ONLY: Simulate a successful payment verification"""
    try:
        parts = reference.split("_")
        user_id = parts[1]
    except:
        raise HTTPException(status_code=400, detail="Invalid reference format")
    
    # Find or create transaction
    transaction = db.query(Transaction).filter(
        Transaction.reference == reference
    ).first()
    
    if not transaction:
        transaction = Transaction(
            user_id=user_id,
            reference=reference,
            plan_id=plan_id,
            amount=5000,
            status=TransactionStatus.PENDING
        )
        db.add(transaction)
    
    # Update transaction
    transaction.status = TransactionStatus.SUCCESS
    transaction.paid_at = "2026-02-12T12:00:00Z"
    transaction.payment_channel = "card"
    
    # Update user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.subscription_tier = plan_id
    
    db.commit()
    
    return {
        "message": "TEST: Payment simulated successfully",
        "plan": plan_id,
        "status": "active",
        "user_email": user.email,
        "note": "This is a test endpoint for development only"
    }
