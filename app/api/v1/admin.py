from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api.deps import get_current_admin, get_db
from app.models.user import User, SubscriptionTier
from app.models.transaction import Transaction, TransactionStatus

router = APIRouter()

@router.get("/dashboard")
def get_dashboard_stats(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics"""
    
    # User stats
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    verified_users = db.query(User).filter(User.is_verified == True).count()
    
    # Subscription stats
    subscription_counts = db.query(
        User.subscription_tier,
        func.count(User.id)
    ).group_by(User.subscription_tier).all()
    
    subscription_stats = {
        tier.value if hasattr(tier, 'value') else tier: count 
        for tier, count in subscription_counts
    }
    
    # Revenue stats
    total_revenue = db.query(
        func.sum(Transaction.amount)
    ).filter(
        Transaction.status == TransactionStatus.SUCCESS
    ).scalar() or 0
    
    monthly_revenue = db.query(
        func.sum(Transaction.amount)
    ).filter(
        Transaction.status == TransactionStatus.SUCCESS,
        Transaction.created_at >= datetime.utcnow().replace(day=1)
    ).scalar() or 0
    
    # Transaction stats
    total_transactions = db.query(Transaction).count()
    successful_transactions = db.query(Transaction).filter(
        Transaction.status == TransactionStatus.SUCCESS
    ).count()
    failed_transactions = db.query(Transaction).filter(
        Transaction.status == TransactionStatus.FAILED
    ).count()
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "verified": verified_users
        },
        "subscriptions": subscription_stats,
        "revenue": {
            "total": float(total_revenue),
            "this_month": float(monthly_revenue)
        },
        "transactions": {
            "total": total_transactions,
            "successful": successful_transactions,
            "failed": failed_transactions
        }
    }

@router.get("/users")
def list_users(
    skip: int = 0,
    limit: int = 100,
    subscription_tier: Optional[SubscriptionTier] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all users with filters"""
    
    query = db.query(User)
    
    # Apply filters
    if subscription_tier:
        query = query.filter(User.subscription_tier == subscription_tier)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if search:
        query = query.filter(
            User.email.ilike(f"%{search}%") | 
            User.full_name.ilike(f"%{search}%")
        )
    
    total = query.count()
    users = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "full_name": u.full_name,
                "subscription_tier": u.subscription_tier.value if hasattr(u.subscription_tier, 'value') else u.subscription_tier,
                "is_active": u.is_active,
                "is_verified": u.is_verified,
                "is_superuser": u.is_superuser,
                "subscription_start_date": u.subscription_start_date.isoformat() if u.subscription_start_date else None,
                "subscription_end_date": u.subscription_end_date.isoformat() if u.subscription_end_date else None,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_login": u.last_login.isoformat() if u.last_login else None
            }
            for u in users
        ]
    }

@router.get("/users/{user_id}")
def get_user_details(
    user_id: str,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get detailed user information"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's transactions
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).order_by(Transaction.created_at.desc()).all()
    
    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "subscription_tier": user.subscription_tier.value if hasattr(user.subscription_tier, 'value') else user.subscription_tier,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "is_superuser": user.is_superuser,
            "auto_renew": user.auto_renew,
            "subscription_start_date": user.subscription_start_date.isoformat() if user.subscription_start_date else None,
            "subscription_end_date": user.subscription_end_date.isoformat() if user.subscription_end_date else None,
            "payment_customer_id": user.payment_customer_id,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
        },
        "transactions": [
            {
                "id": str(t.id),
                "reference": t.reference,
                "amount": float(t.amount),
                "currency": t.currency,
                "status": t.status.value if hasattr(t.status, 'value') else t.status,
                "plan_id": t.plan_id,
                "payment_channel": t.payment_channel,
                "paid_at": t.paid_at.isoformat() if t.paid_at else None,
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in transactions
        ]
    }

@router.patch("/users/{user_id}/subscription")
def update_user_subscription(
    user_id: str,
    subscription_tier: SubscriptionTier,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Manually update user subscription (admin only)"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_tier = user.subscription_tier
    user.subscription_tier = subscription_tier
    
    # Update dates if upgrading from free
    if old_tier == SubscriptionTier.FREE and subscription_tier != SubscriptionTier.FREE:
        user.subscription_start_date = datetime.utcnow()
        user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
    # Clear dates if downgrading to free
    elif subscription_tier == SubscriptionTier.FREE:
        user.subscription_start_date = None
        user.subscription_end_date = None
    
    db.commit()
    
    return {
        "message": "Subscription updated",
        "user_id": str(user.id),
        "email": user.email,
        "old_tier": old_tier.value if hasattr(old_tier, 'value') else old_tier,
        "new_tier": subscription_tier.value if hasattr(subscription_tier, 'value') else subscription_tier
    }

@router.post("/users/{user_id}/verify")
def verify_user(
    user_id: str,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Manually verify user email"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_verified = True
    db.commit()
    
    return {
        "message": "User verified",
        "user_id": str(user.id),
        "email": user.email
    }

@router.get("/transactions")
def list_transactions(
    skip: int = 0,
    limit: int = 100,
    status: Optional[TransactionStatus] = None,
    plan_id: Optional[str] = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all transactions with filters"""
    
    query = db.query(Transaction).join(User)
    
    if status:
        query = query.filter(Transaction.status == status)
    
    if plan_id:
        query = query.filter(Transaction.plan_id == plan_id)
    
    total = query.count()
    transactions = query.order_by(
        Transaction.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "transactions": [
            {
                "id": str(t.id),
                "user_id": str(t.user_id),
                "user_email": t.user.email if t.user else None,
                "reference": t.reference,
                "amount": float(t.amount),
                "currency": t.currency,
                "status": t.status.value if hasattr(t.status, 'value') else t.status,
                "plan_id": t.plan_id,
                "payment_channel": t.payment_channel,
                "paid_at": t.paid_at.isoformat() if t.paid_at else None,
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in transactions
        ]
    }

@router.get("/revenue")
def get_revenue_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get revenue report with date range"""
    
    query = db.query(Transaction).filter(
        Transaction.status == TransactionStatus.SUCCESS
    )
    
    if start_date:
        query = query.filter(Transaction.created_at >= start_date)
    
    if end_date:
        query = query.filter(Transaction.created_at <= end_date)
    
    total_revenue = query.with_entities(func.sum(Transaction.amount)).scalar() or 0
    
    # Revenue by plan
    revenue_by_plan = query.with_entities(
        Transaction.plan_id,
        func.sum(Transaction.amount),
        func.count(Transaction.id)
    ).group_by(Transaction.plan_id).all()
    
    # Daily revenue (last 30 days)
    daily_revenue = db.query(
        func.date(Transaction.created_at),
        func.sum(Transaction.amount)
    ).filter(
        Transaction.status == TransactionStatus.SUCCESS,
        Transaction.created_at >= datetime.utcnow() - timedelta(days=30)
    ).group_by(func.date(Transaction.created_at)).all()
    
    return {
        "total_revenue": float(total_revenue),
        "revenue_by_plan": [
            {
                "plan_id": plan,
                "revenue": float(rev),
                "transactions": count
            }
            for plan, rev, count in revenue_by_plan
        ],
        "daily_revenue": [
            {
                "date": str(date),
                "revenue": float(rev)
            }
            for date, rev in daily_revenue
        ]
    }
