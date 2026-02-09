from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.database import get_db
from app.models import User, Transaction, TransactionStatus
from app.schemas import (
    AdminUsersListResponse, AdminUserResponse,
    AdminTransactionsListResponse, AdminTransactionResponse
)
from app.dependencies import get_admin_user

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.get("/users", response_model=AdminUsersListResponse)
def get_all_users(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)."""
    # Get total count
    total = db.query(func.count(User.id)).scalar()

    # Get paginated users
    offset = (page - 1) * limit
    users = db.query(User).order_by(User.created_at.desc()).offset(offset).limit(limit).all()

    return AdminUsersListResponse(
        total=total,
        page=page,
        limit=limit,
        users=[AdminUserResponse.model_validate(u) for u in users]
    )


@router.get("/transactions", response_model=AdminTransactionsListResponse)
def get_all_transactions(
    status: Optional[TransactionStatus] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get all transactions (admin only)."""
    # Build query
    query = db.query(Transaction, User.email).join(User)

    if status:
        query = query.filter(Transaction.status == status)

    # Get total count
    total = query.count()

    # Get paginated transactions
    offset = (page - 1) * limit
    results = query.order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()

    transactions = []
    for transaction, user_email in results:
        transactions.append(AdminTransactionResponse(
            id=transaction.id,
            reference=transaction.reference,
            user_email=user_email,
            amount=transaction.amount,
            currency=transaction.currency,
            status=transaction.status,
            created_at=transaction.created_at,
            verified_at=transaction.verified_at
        ))

    return AdminTransactionsListResponse(
        total=total,
        page=page,
        limit=limit,
        transactions=transactions
    )
