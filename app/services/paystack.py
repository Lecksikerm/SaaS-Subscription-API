import hmac
import hashlib
import requests
from typing import Dict, Optional
from app.core.config import settings

class PaystackService:
    BASE_URL = "https://api.paystack.co"
    
    @staticmethod
    def _get_headers():
        return {
            "Authorization": f"Bearer {settings.paystack_secret_key}",
            "Content-Type": "application/json"
        }
    
    @classmethod
    def initialize_transaction(cls, email: str, amount: int, reference: str, 
                               callback_url: Optional[str] = None, 
                               metadata: Optional[Dict] = None) -> Dict:
        url = f"{cls.BASE_URL}/transaction/initialize"
        payload = {
            "email": email,
            "amount": amount,
            "reference": reference,
            "callback_url": callback_url,
            "metadata": metadata or {}
        }
        response = requests.post(url, json=payload, headers=cls._get_headers())
        return response.json()
    
    @classmethod
    def verify_transaction(cls, reference: str) -> Dict:
        url = f"{cls.BASE_URL}/transaction/verify/{reference}"
        response = requests.get(url, headers=cls._get_headers())
        return response.json()
    
    @classmethod
    def verify_webhook_signature(cls, signature: str, request_body: bytes) -> bool:
        """Verify Paystack webhook signature"""
        # Skip verification if no webhook secret configured (development only)
        if not settings.paystack_webhook_secret or settings.paystack_webhook_secret == "pk_test_554587fd3e6761ebd3ced3696ea9f9d010c154f6":
            return True
        
        expected_signature = hmac.new(
            settings.paystack_webhook_secret.encode(),
            request_body,
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
