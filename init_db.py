import os
import sys
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.models import User, Transaction

print(f"🔍 DATABASE_URL: {settings.database_url[:60]}...")

print("📊 Creating tables...")
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created!")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
