import httpx
import hmac
import hashlib
import secrets
import time
from datetime import datetime, timezone
from typing import Optional
from app.config import get_settings

settings = get_settings()

PAYSTACK_BASE_URL = "https://api.paystack.co"


def is_mock_mode() -> bool:
    """Check if we should use mock mode (no real Paystack keys)."""
    key = settings.PAYSTACK_SECRET_KEY
    return not key or key.startswith("sk_test_xxxxx") or key == "sk_test_xxxxx"


def generate_reference() -> str:
    """Generate a unique transaction reference."""
    timestamp = int(time.time())
    random_str = secrets.token_hex(4).upper()
    return f"TXN_{timestamp}_{random_str}"


async def initialize_transaction(email: str, amount: int, reference: str) -> dict:
    """
    Initialize a Paystack transaction.

    Args:
        email: Customer email address
        amount: Amount in kobo (smallest currency unit)
        reference: Unique transaction reference

    Returns:
        Paystack API response data
    """
    if is_mock_mode():
        # Return mock response
        access_code = secrets.token_hex(8)
        return {
            "status": True,
            "message": "Authorization URL created (MOCK MODE)",
            "data": {
                "authorization_url": f"https://checkout.paystack.com/mock_{access_code}",
                "access_code": access_code,
                "reference": reference
            }
        }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYSTACK_BASE_URL}/transaction/initialize",
            headers={
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "email": email,
                "amount": str(amount),
                "reference": reference
            }
        )
        response.raise_for_status()
        return response.json()


async def verify_transaction(reference: str) -> dict:
    """
    Verify a Paystack transaction.

    Args:
        reference: Transaction reference to verify

    Returns:
        Paystack API response data
    """
    if is_mock_mode():
        # Return mock successful response
        return {
            "status": True,
            "message": "Verification successful (MOCK MODE)",
            "data": {
                "reference": reference,
                "amount": 500000,  # Will be overwritten by actual DB amount
                "currency": "NGN",
                "status": "success",
                "paid_at": datetime.now(timezone.utc).isoformat(),
                "customer": {
                    "email": "mock@example.com"
                }
            }
        }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}",
            headers={
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"
            }
        )
        response.raise_for_status()
        return response.json()


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify Paystack webhook signature.

    Args:
        payload: Raw request body
        signature: X-Paystack-Signature header value

    Returns:
        True if signature is valid, False otherwise
    """
    if is_mock_mode():
        return True  # Skip verification in mock mode

    if not settings.PAYSTACK_WEBHOOK_SECRET:
        return True  # Skip verification if secret not configured

    expected_signature = hmac.new(
        settings.PAYSTACK_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha512
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)
