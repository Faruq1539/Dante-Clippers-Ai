from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.credit_transaction import CreditTransaction
from app.schemas.credit import CreditBalanceOut, CreditTransactionOut

router = APIRouter(prefix="/credits", tags=["credits"])


@router.get("/balance", response_model=CreditBalanceOut)
def get_balance(current_user: User = Depends(get_current_user)):
    return CreditBalanceOut(
        credit_balance=current_user.credit_balance,
        credit_renews_at=current_user.credit_renews_at,
    )


@router.get("/transactions", response_model=list[CreditTransactionOut])
def list_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(CreditTransaction)
        .filter(CreditTransaction.user_id == current_user.id)
        .order_by(CreditTransaction.created_at.desc())
        .all()
    )
