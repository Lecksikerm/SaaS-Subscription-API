from typing import Dict, Any

SUBSCRIPTION_PLANS = {
    "free": {
        "name": "Free",
        "price": 0,
        "currency": "NGN",
        "features": ["Basic access", "Limited storage"],
        "paystack_plan_code": None
    },
    "basic": {
        "name": "Basic",
        "price": 5000,
        "currency": "NGN",
        "features": ["Full access", "10GB storage", "Email support"],
        "paystack_plan_code": "PLN_basic_monthly"
    },
    "pro": {
        "name": "Pro",
        "price": 15000,
        "currency": "NGN",
        "features": ["Everything in Basic", "100GB storage", "Priority support", "API access"],
        "paystack_plan_code": "PLN_pro_monthly"
    },
    "enterprise": {
        "name": "Enterprise",
        "price": 50000,
        "currency": "NGN",
        "features": ["Everything in Pro", "Unlimited storage", "Dedicated support"],
        "paystack_plan_code": "PLN_enterprise_monthly"
    }
}

def get_plan(plan_id: str) -> Dict[str, Any]:
    return SUBSCRIPTION_PLANS.get(plan_id)

def get_all_plans() -> Dict[str, Any]:
    return SUBSCRIPTION_PLANS
