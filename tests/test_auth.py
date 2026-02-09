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


class TestUserRegistration:
    def test_register_success(self):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert data["role"] == "user"

    def test_register_duplicate_email(self):
        # First registration
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "SecurePass123!",
                "full_name": "Test User"
            }
        )
        # Second registration with same email
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "SecurePass123!",
                "full_name": "Another User"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_weak_password(self):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "weak",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 422


class TestUserLogin:
    def test_login_success(self):
        # Register user first
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "password": "SecurePass123!",
                "full_name": "Test User"
            }
        )
        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "login@example.com",
                "password": "SecurePass123!"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "login@example.com"

    def test_login_wrong_password(self):
        # Register user first
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrongpass@example.com",
                "password": "SecurePass123!",
                "full_name": "Test User"
            }
        )
        # Login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "wrongpass@example.com",
                "password": "WrongPassword123!"
            }
        )
        assert response.status_code == 401


class TestUserProfile:
    def test_get_profile_success(self):
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "profile@example.com",
                "password": "SecurePass123!",
                "full_name": "Profile User"
            }
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "profile@example.com",
                "password": "SecurePass123!"
            }
        )
        token = login_response.json()["access_token"]

        # Get profile
        response = client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "profile@example.com"
        assert data["full_name"] == "Profile User"

    def test_get_profile_no_token(self):
        response = client.get("/api/v1/auth/profile")
        assert response.status_code == 403
