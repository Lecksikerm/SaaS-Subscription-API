from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User, SubscriptionTier

def check_expired_subscriptions():
    """Check and downgrade expired subscriptions"""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        
        # Find users with expired paid subscriptions
        expired_users = db.query(User).filter(
            User.subscription_tier != SubscriptionTier.FREE,
            User.subscription_end_date < now,
            User.auto_renew == False  
        ).all()
        
        for user in expired_users:
            print(f"Downgrading user {user.email} from {user.subscription_tier} to free")
            user.subscription_tier = SubscriptionTier.FREE
            user.subscription_start_date = None
            user.subscription_end_date = None
        
        db.commit()
        return len(expired_users)
    finally:
        db.close()

def notify_expiring_subscriptions(days_before: int = 3):
    """Notify users of upcoming expiration"""
    db = SessionLocal()
    try:
        threshold = datetime.utcnow() + timedelta(days=days_before)
        
        expiring_users = db.query(User).filter(
            User.subscription_tier != SubscriptionTier.FREE,
            User.subscription_end_date <= threshold,
            User.subscription_end_date > datetime.utcnow()
        ).all()
        
        for user in expiring_users:
            days_left = (user.subscription_end_date - datetime.utcnow()).days
            print(f"User {user.email} subscription expires in {days_left} days")
            # TODO: Send email notification
        
        return len(expiring_users)
    finally:
        db.close()
