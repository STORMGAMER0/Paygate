# PayGate API

A production-ready payment gateway API built with FastAPI and Paystack integration.

## Overview

PayGate API is a backend system demonstrating comprehensive backend development skills through a real-world payment processing platform. It integrates Paystack (Nigeria's leading payment gateway) with robust authentication, authorization, and database management.

## Features

- **Authentication with JWT** - Secure user registration and login
- **Paystack Payment Integration** - Initialize and verify payments
- **Webhook Handler** - Process Paystack payment events
- **Admin Dashboard Endpoints** - View all users and transactions
- **Payment History** - Paginated transaction history per user
- **Role-Based Access Control** - User and Admin permissions

## Tech Stack

- **Language:** Python 3.9+
- **Framework:** FastAPI
- **Database:** PostgreSQL 14+
- **ORM:** SQLAlchemy
- **Authentication:** JWT (python-jose)
- **Password Hashing:** Passlib with bcrypt
- **Payment Gateway:** Paystack API

## Prerequisites

- Python 3.9+
- PostgreSQL 14+
- Paystack account (test mode)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/paygate-api.git
   cd paygate-api
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

5. **Create database**
   ```bash
   createdb paygate  # PostgreSQL must be running
   ```

6. **Start server**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Test API**

   Visit http://localhost:8000/docs

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/paygate` |
| `SECRET_KEY` | JWT secret key (min 32 chars) | `your-secret-key-here` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | `1440` |
| `PAYSTACK_SECRET_KEY` | Paystack secret key | `sk_test_xxxxx` |
| `PAYSTACK_PUBLIC_KEY` | Paystack public key | `pk_test_xxxxx` |
| `PAYSTACK_WEBHOOK_SECRET` | Webhook signature secret | `whsec_xxxxx` |

## API Documentation

Once running, access the interactive API documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### API Endpoints

#### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get token |
| GET | `/api/v1/auth/profile` | Get current user profile |

#### Payments
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/payments/initialize` | Initialize payment |
| GET | `/api/v1/payments/verify/{reference}` | Verify payment |
| POST | `/api/v1/payments/webhook` | Paystack webhook handler |
| GET | `/api/v1/payments/history` | Get payment history |

#### Admin (Admin role required)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/users` | Get all users |
| GET | `/api/v1/admin/transactions` | Get all transactions |

#### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |

## Testing

Run tests with pytest:
```bash
pip install pytest
pytest tests/ -v
```

### Manual Testing Checklist

**Authentication:**
- [ ] Register new user
- [ ] Login with correct credentials
- [ ] Login with wrong credentials (should fail)
- [ ] Access protected endpoint with token
- [ ] Access protected endpoint without token (should fail)

**Payments:**
- [ ] Initialize payment
- [ ] Complete payment with test card
- [ ] Verify payment status
- [ ] Check payment appears in history

**Admin:**
- [ ] Get all users (as admin)
- [ ] Get all transactions (as admin)
- [ ] Try admin endpoints as regular user (should fail)

### Test Cards (Paystack)

**Successful Payment:**
- Card: 4084 0840 8408 4081
- CVV: 408
- Expiry: 12/26
- PIN: 0000

**Failed Payment:**
- Card: 5060 6666 6666 6666 666

## Project Structure

```
paygate-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration and settings
│   ├── database.py          # Database connection and session
│   ├── models.py            # SQLAlchemy database models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── dependencies.py      # Reusable dependencies
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── utils.py         # JWT creation, password hashing
│   │   └── routes.py        # Authentication endpoints
│   ├── payments/
│   │   ├── __init__.py
│   │   ├── paystack.py      # Paystack integration utilities
│   │   └── routes.py        # Payment endpoints
│   └── admin/
│       ├── __init__.py
│       └── routes.py        # Admin-only endpoints
├── tests/
│   ├── __init__.py
│   ├── test_auth.py
│   └── test_payments.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Deployment

### Render.com (Free Tier)

1. Push code to GitHub repository
2. Create Render.com account
3. Create new Web Service
4. Connect GitHub repository
5. Add PostgreSQL database
6. Configure environment variables
7. Deploy

**Build Command:** `pip install -r requirements.txt`

**Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## License

MIT

## Author

Obi Ebubechukwu - [eobi816@gmail.com](mailto:eobi816@gmail.com)
