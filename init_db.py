from app.db.base import Base
from app.db.session import engine
from app.models import User, Transaction

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("✅ Tables created!")