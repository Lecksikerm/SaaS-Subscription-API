from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    app_name: str = "SaaS Subscription API"
    debug: bool = False
    
    # Database - Render will provide this
    database_url: str = "postgresql://postgres:postgres@localhost:5432/saas_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # JWT
    secret_key: str = "change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    # Paystack
    paystack_secret_key: str = ""
    paystack_webhook_secret: str = ""

    class Config:
        env_file = ".env"
        # Allow extra fields from environment
        extra = "ignore"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Fix Render's postgres:// URL to postgresql://
        if self.database_url and self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql://", 1)

settings = Settings()
