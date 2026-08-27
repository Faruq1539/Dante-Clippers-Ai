"""
Credit accounting logic.

Per the product spec (docs/tech-spec.md, section 8): credits are spent based
on SOURCE VIDEO DURATION PROCESSED, not on the number of clips generated.
A 2-hour podcast costs more to process than a 5-minute video regardless of
how many clips come out of it -- pricing should track that, not clip count.
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.credit_transaction import CreditTransaction

# Rough placeholder rate -- tune this against real compute cost per minute
# of source video (transcription + LLM scoring + render) once you have
# production usage data. See docs/tech-spec.md section 8 for the framing.
CREDITS_PER_MINUTE_OF_SOURCE_VIDEO = 2


def credits_required_for_duration(duration_seconds: int) -> int:
    minutes = max(1, round(duration_seconds / 60))
    return minutes * CREDITS_PER_MINUTE_OF_SOURCE_VIDEO


def charge_for_processing(db: Session, user: User, duration_seconds: int) -> None:
    """Deduct credits for processing a source video of the given duration.

    Raises HTTPException(402) if the user doesn't have enough credits.
    Call this BEFORE enqueuing the processing job, not after, so you never
    do compute work you can't bill for.
    """
    cost = credits_required_for_duration(duration_seconds)

    if user.credit_balance < cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Not enough credits: need {cost}, have {user.credit_balance}",
        )

    user.credit_balance -= cost
    db.add(
        CreditTransaction(
            user_id=user.id,
            amount=-cost,
            reason="spend_processing",
        )
    )
    db.commit()


def grant_monthly_credits(db: Session, user: User, amount: int) -> None:
    """Called by a scheduled job on the user's renewal date."""
    user.credit_balance += amount
    db.add(
        CreditTransaction(
            user_id=user.id,
            amount=amount,
            reason="monthly_grant",
        )
    )
    db.commit()


def grant_purchased_credits(db: Session, user: User, amount: int) -> None:
    """Called after a verified App Store / Play Store IAP receipt.

    IMPORTANT: only call this after verifying the purchase receipt
    server-side with Apple/Google -- never trust a client-reported
    purchase amount directly.
    """
    user.credit_balance += amount
    db.add(
        CreditTransaction(
            user_id=user.id,
            amount=amount,
            reason="purchase",
        )
    )
    db.commit()
