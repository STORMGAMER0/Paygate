from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional, List
from app.models import UserRole, TransactionStatus
import re


# ============== User Schemas ==============

class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    """Schema for user profile response."""
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Token Schemas ==============

class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Schema for JWT token payload."""
    sub: int
    email: str
    role: UserRole
    exp: datetime


# ============== Payment Schemas ==============

class PaymentInitialize(BaseModel):
    """Schema for payment initialization request."""
    amount: int = Field(..., gt=0, description="Amount in kobo")
    currency: str = Field(default="NGN", max_length=3)


class PaymentInitializeResponse(BaseModel):
    """Schema for payment initialization response."""
    status: str
    reference: str
    authorization_url: str
    access_code: str
    amount: int
    currency: str


class PaymentVerifyResponse(BaseModel):
    """Schema for payment verification response."""
    status: str
    reference: str
    amount: int
    currency: str
    payment_status: str
    paid_at: Optional[datetime] = None
    customer_email: str


class TransactionResponse(BaseModel):
    """Schema for transaction response."""
    id: int
    reference: str
    amount: int
    currency: str
    status: TransactionStatus
    created_at: datetime
    verified_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentHistoryResponse(BaseModel):
    """Schema for paginated payment history."""
    total: int
    page: int
    limit: int
    payments: List[TransactionResponse]


# ============== Admin Schemas ==============

class AdminUserResponse(BaseModel):
    """Schema for admin user list response."""
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AdminUsersListResponse(BaseModel):
    """Schema for paginated admin users list."""
    total: int
    page: int
    limit: int
    users: List[AdminUserResponse]


class AdminTransactionResponse(BaseModel):
    """Schema for admin transaction response."""
    id: int
    reference: str
    user_email: str
    amount: int
    currency: str
    status: TransactionStatus
    created_at: datetime
    verified_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminTransactionsListResponse(BaseModel):
    """Schema for paginated admin transactions list."""
    total: int
    page: int
    limit: int
    transactions: List[AdminTransactionResponse]


# ============== Webhook Schemas ==============

class WebhookPayload(BaseModel):
    """Schema for Paystack webhook payload."""
    event: str
    data: dict


# ============== Health Check ==============

class HealthCheck(BaseModel):
    """Schema for health check response."""
    status: str
    database: str
    timestamp: datetime
