from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from typing import Optional
from app.database import get_db
from app.models import User, Transaction, TransactionStatus
from app.schemas import (
    PaymentInitialize, PaymentInitializeResponse, PaymentVerifyResponse,
    PaymentHistoryResponse, TransactionResponse, WebhookPayload
)
from app.dependencies import get_current_user
from app.payments.paystack import (
    generate_reference, initialize_transaction, verify_transaction,
    verify_webhook_signature
)

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


@router.post("/initialize", response_model=PaymentInitializeResponse)
async def initialize_payment(
    payment: PaymentInitialize,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initialize a new payment transaction."""
    reference = generate_reference()

    try:
        # Call Paystack API
        paystack_response = await initialize_transaction(
            email=current_user.email,
            amount=payment.amount,
            reference=reference
        )

        if not paystack_response.get("status"):
            raise HTTPException(
                status_code=status.HTTP_424_FAILED_DEPENDENCY,
                detail="Payment initialization failed"
            )

        data = paystack_response["data"]

        # Store transaction in database
        transaction = Transaction(
            user_id=current_user.id,
            reference=reference,
            amount=payment.amount,
            currency=payment.currency,
            status=TransactionStatus.PENDING,
            paystack_response=paystack_response
        )
        db.add(transaction)
        db.commit()

        return PaymentInitializeResponse(
            status="success",
            reference=reference,
            authorization_url=data["authorization_url"],
            access_code=data["access_code"],
            amount=payment.amount,
            currency=payment.currency
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment initialization failed: {str(e)}"
        )


@router.get("/verify/{reference}", response_model=PaymentVerifyResponse)
async def verify_payment(
    reference: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify a payment transaction."""
    # Find transaction in database
    transaction = db.query(Transaction).filter(
        Transaction.reference == reference,
        Transaction.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    try:
        # Call Paystack verify API
        paystack_response = await verify_transaction(reference)

        if not paystack_response.get("status"):
            raise HTTPException(
                status_code=status.HTTP_424_FAILED_DEPENDENCY,
                detail="Payment verification failed"
            )

        data = paystack_response["data"]
        paystack_status = data.get("status", "").lower()

        # Update transaction status
        if paystack_status == "success":
            transaction.status = TransactionStatus.SUCCESS
        elif paystack_status in ["failed", "abandoned"]:
            transaction.status = TransactionStatus.FAILED
        # else keep as pending

        transaction.paystack_response = paystack_response
        transaction.verified_at = datetime.now(timezone.utc)
        db.commit()

        paid_at = None
        if data.get("paid_at"):
            try:
                paid_at = datetime.fromisoformat(data["paid_at"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        return PaymentVerifyResponse(
            status="success",
            reference=reference,
            amount=data.get("amount", transaction.amount),
            currency=data.get("currency", transaction.currency),
            payment_status=paystack_status,
            paid_at=paid_at,
            customer_email=current_user.email
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment verification failed: {str(e)}"
        )


@router.post("/webhook")
async def handle_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Paystack webhook events."""
    # Get raw body and signature
    body = await request.body()
    signature = request.headers.get("x-paystack-signature", "")

    # Verify webhook signature
    if not verify_webhook_signature(body, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )

    # Parse payload
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )

    event = payload.get("event")
    data = payload.get("data", {})
    reference = data.get("reference")

    if not reference:
        return {"status": "webhook received"}

    # Find transaction
    transaction = db.query(Transaction).filter(
        Transaction.reference == reference
    ).first()

    if transaction:
        # Update status based on event
        if event == "charge.success":
            transaction.status = TransactionStatus.SUCCESS
            transaction.verified_at = datetime.now(timezone.utc)
        elif event == "charge.failed":
            transaction.status = TransactionStatus.FAILED

        transaction.paystack_response = payload
        db.commit()

    return {"status": "webhook received"}


@router.get("/history", response_model=PaymentHistoryResponse)
def get_payment_history(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's payment history."""
    # Get total count
    total = db.query(func.count(Transaction.id)).filter(
        Transaction.user_id == current_user.id
    ).scalar()

    # Get paginated transactions
    offset = (page - 1) * limit
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()

    return PaymentHistoryResponse(
        total=total,
        page=page,
        limit=limit,
        payments=[TransactionResponse.model_validate(t) for t in transactions]
    )
