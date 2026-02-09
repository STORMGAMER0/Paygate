import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base, get_db

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def get_auth_token():
    """Helper to get auth token."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "payment@example.com",
            "password": "SecurePass123!",
            "full_name": "Payment User"
        }
    )
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "payment@example.com",
            "password": "SecurePass123!"
        }
    )
    return response.json()["access_token"]


class TestPaymentHistory:
    def test_get_payment_history_empty(self):
        token = get_auth_token()
        response = client.get(
            "/api/v1/payments/history",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["payments"] == []

    def test_get_payment_history_no_auth(self):
        response = client.get("/api/v1/payments/history")
        assert response.status_code == 403


class TestPaymentInitialize:
    def test_initialize_payment_no_auth(self):
        response = client.post(
            "/api/v1/payments/initialize",
            json={"amount": 5000, "currency": "NGN"}
        )
        assert response.status_code == 403

    def test_initialize_payment_invalid_amount(self):
        token = get_auth_token()
        response = client.post(
            "/api/v1/payments/initialize",
            json={"amount": 0, "currency": "NGN"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 422


class TestPaymentVerify:
    def test_verify_nonexistent_transaction(self):
        token = get_auth_token()
        response = client.get(
            "/api/v1/payments/verify/NONEXISTENT_REF",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404


class TestWebhook:
    def test_webhook_invalid_payload(self):
        response = client.post(
            "/api/v1/payments/webhook",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400

    def test_webhook_valid_payload(self):
        response = client.post(
            "/api/v1/payments/webhook",
            json={
                "event": "charge.success",
                "data": {
                    "reference": "TEST_REF_123",
                    "amount": 5000,
                    "status": "success"
                }
            }
        )
        assert response.status_code == 200
        assert response.json()["status"] == "webhook received"
