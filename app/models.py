from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, JSON, CheckConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_users_email", "email", unique=True),
        Index("idx_users_role", "role"),
    )


class IdempotencyKey(Base):
    """Store idempotency keys to prevent duplicate payments."""

    __tablename__ = "idempotency_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    response = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("idx_idempotency_key", "key", unique=True),
        Index("idx_idempotency_user_id", "user_id"),
    )


class Transaction(Base):
    """Transaction model for payment records."""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reference = Column(String(100), unique=True, nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # Amount in kobo (smallest currency unit)
    currency = Column(String(3), default="NGN")
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    paystack_response = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="transactions")

    __table_args__ = (
        CheckConstraint("amount > 0", name="check_positive_amount"),
        Index("idx_transactions_reference", "reference", unique=True),
        Index("idx_transactions_user_id", "user_id"),
        Index("idx_transactions_status", "status"),
        Index("idx_transactions_created_at", "created_at"),
    )
