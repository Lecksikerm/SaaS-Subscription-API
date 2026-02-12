from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str
    debug: bool
    database_url: str
    
    redis_url: str = "redis://localhost:6379/0"  

    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    paystack_secret_key: str
    paystack_webhook_secret: str

    class Config:
        env_file = ".env"

settings = Settings()
