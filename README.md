# 🚀 SaaS Subscription API

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Paystack](https://img.shields.io/badge/Paystack-00C3F7?style=for-the-badge&logo=stripe&logoColor=white)

**Production-ready SaaS billing backend with Paystack integration**

[📖 Documentation](#documentation) • [🚀 Quick Start](#quick-start) • [📡 API Reference](#api-reference)

</div>

---

## ✨ Features

| Feature | Description | Status |
|---------|-------------|--------|
| 🔐 **Authentication** | JWT-based auth with secure password hashing | ✅ |
| 💳 **Payments** | Paystack integration for Nigerian NGN payments | ✅ |
| 📅 **Subscriptions** | Multi-tier plans (Free, Basic, Pro, Enterprise) | ✅ |
| 🔔 **Webhooks** | Automatic payment verification | ✅ |
| 📊 **Admin Dashboard** | View users, transactions, revenue reports | ✅ |
| 📝 **Transaction History** | Complete payment records | ✅ |
| ⏰ **Subscription Dates** | Start/end dates with expiration tracking | ✅ |
| 🔄 **Auto-Renewal** | Optional automatic subscription renewal | ✅ |

---

## 🏗️ Architecture
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   FastAPI App   │────▶│   PostgreSQL    │     │     Redis       │
│   (Port 8000)   │     │   (Port 5434)   │     │   (Port 6380)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
│
▼
┌─────────────────┐
│   Paystack API  │
│  (Payment GW)   │
└─────────────────┘
plain
Copy

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Paystack account (test keys)

### 1️⃣ Clone & Setup

```bash
# Clone repository
git clone https://github.com/yourusername/saas-subscription-api.git
cd saas-subscription-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
2️⃣ Environment Variables
Create .env file:
env
Copy
APP_NAME=SaaS Subscription API
DEBUG=True

# Database (Port 5434 to avoid conflicts)
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5434/saas_db

# Redis (Port 6380 to avoid conflicts)
REDIS_URL=redis://localhost:6380/0

# JWT
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Paystack (Get from https://dashboard.paystack.com)
PAYSTACK_SECRET_KEY=sk_test_your_key_here
PAYSTACK_WEBHOOK_SECRET=whsec_your_webhook_secret
3️⃣ Start Services
bash
Copy
# Start PostgreSQL & Redis
docker compose up -d db redis

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
🎉 API is live at http://localhost:8000
📚 Interactive docs at http://localhost:8000/docs
📡 API Reference
🔐 Authentication
Table
Copy
Endpoint	Method	Description	Auth
/api/v1/auth/register	POST	Create new account	❌
/api/v1/auth/login	POST	Get JWT token	❌
Register:
bash
Copy
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secret123",
    "full_name": "John Doe"
  }'
Login:
bash
Copy
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secret123"
  }'
Response:
JSON
Copy
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
👤 User Profile
Table
Copy
Endpoint	Method	Description	Auth
/api/v1/users/me	GET	Get profile	✅
/api/v1/users/me	PATCH	Update profile	✅
💳 Subscriptions
Table
Copy
Endpoint	Method	Description	Auth
/api/v1/subscriptions/plans	GET	List all plans	✅
/api/v1/subscriptions/subscribe/{plan}	POST	Start payment	✅
/api/v1/subscriptions/status	GET	Check subscription	✅
/api/v1/subscriptions/history	GET	Payment history	✅
/api/v1/subscriptions/cancel	POST	Cancel renewal	✅
Subscribe to Pro:
bash
Copy
curl -X POST "http://localhost:8000/api/v1/subscriptions/subscribe/pro" \
  -H "Authorization: Bearer YOUR_TOKEN"
Response:
JSON
Copy
{
  "authorization_url": "https://checkout.paystack.com/...",
  "reference": "sub_xxx_xxxxxx",
  "plan": "pro",
  "amount": 15000
}
🔧 Admin (Superuser Only)
Table
Copy
Endpoint	Method	Description
/api/v1/admin/dashboard	GET	Dashboard stats
/api/v1/admin/users	GET	List all users
/api/v1/admin/users/{id}	GET	User details
/api/v1/admin/users/{id}/subscription	PATCH	Update subscription
/api/v1/admin/transactions	GET	All transactions
/api/v1/admin/revenue	GET	Revenue reports
💰 Subscription Plans
Table
Copy
Plan	Price	Features
🆓 Free	₦0	Basic access, Limited storage
⭐ Basic	₦5,000/mo	Full access, 10GB storage, Email support
🚀 Pro	₦15,000/mo	100GB storage, Priority support, API access
🏢 Enterprise	₦50,000/mo	Unlimited storage, Dedicated support, Custom integrations
🧪 Testing with Paystack
Test Card
plain
Copy
Card Number: 4084084084084081
Expiry: Any future date
CVV: 408
PIN: 0000
OTP: 123456
Webhook Testing (Local)
bash
Copy
# Install ngrok
ngrok http 8000

# Use https URL in Paystack dashboard
# https://xxxxx.ngrok-free.app/api/v1/webhooks/paystack
🐳 Docker Deployment
bash
Copy
# Start all services
docker compose up -d

# View logs
docker compose logs -f app

# Stop
docker compose down
📁 Project Structure
plain
Copy
saas-subscription-api/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py          # Authentication
│   │       ├── users.py         # User profile
│   │       ├── subscriptions.py # Payments & plans
│   │       ├── admin.py         # Admin dashboard
│   │       └── webhooks.py      # Paystack webhooks
│   ├── core/
│   │   ├── config.py            # Settings
│   │   ├── security.py          # Password & JWT
│   │   └── plans.py             # Subscription plans
│   ├── models/
│   │   ├── user.py              # User model
│   │   └── transaction.py       # Payment records
│   ├── services/
│   │   ├── auth.py              # Auth logic
│   │   └── paystack.py          # Paystack API
│   ├── tasks/                   # Celery tasks (ready)
│   └── main.py                  # FastAPI app
├── alembic/                     # Database migrations
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
🔒 Security Checklist
[x] Password hashing (bcrypt)
[x] JWT tokens with expiration
[x] Webhook signature verification
[x] Admin role protection
[x] SQL injection protection (SQLAlchemy)
[x] CORS configuration ready
🚀 Production Deployment
Render (Recommended)
Push to GitHub
Connect to Render
Add environment variables
Deploy!
Environment Variables (Production)
env
Copy
DEBUG=False
SECRET_KEY=strong-random-key-here
DATABASE_URL=postgresql://...
PAYSTACK_SECRET_KEY=sk_live_...
PAYSTACK_WEBHOOK_SECRET=whsec_...
📝 License
MIT License - feel free to use for your SaaS!
🙏 Credits
Built with:
FastAPI - Modern web framework
Paystack - African payments
SQLAlchemy - Database ORM
PostgreSQL - Database
<div align="center">
Made with ❤️ for African SaaS builders
⬆ Back to Top
</div>
```