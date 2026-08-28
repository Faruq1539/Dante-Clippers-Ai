from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.connected_account import ConnectedAccount

router = APIRouter(prefix="/connected-accounts", tags=["connected-accounts"])

SUPPORTED_PLATFORMS = {"tiktok", "instagram", "twitch", "x", "youtube"}


@router.get("")
def list_connected_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    accounts = db.query(ConnectedAccount).filter(ConnectedAccount.user_id == current_user.id).all()
    return [
        {"id": a.id, "platform": a.platform, "platform_username": a.platform_username}
        for a in accounts
    ]


@router.delete("/{account_id}")
def disconnect_account(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    App Store / Play Store both require a clear in-app way to disconnect
    a linked account and delete associated data -- see docs/tech-spec.md
    section 9 (compliance checklist). This endpoint is that mechanism;
    make sure the mobile app surfaces it prominently in settings.
    """
    account = (
        db.query(ConnectedAccount)
        .filter(ConnectedAccount.id == account_id, ConnectedAccount.user_id == current_user.id)
        .first()
    )
    if not account:
        raise HTTPException(status_code=404, detail="Connected account not found")

    # TODO: also revoke the token with the platform itself where their
    # API supports it (e.g. TikTok/Meta token revocation endpoints),
    # not just delete our local record.
    db.delete(account)
    db.commit()
    return {"status": "disconnected"}


@router.get("/oauth/{platform}/start")
def start_oauth(platform: str):
    if platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")
    # TODO: build the real authorization URL per platform (client_id,
    # redirect_uri, scopes, state) and redirect the user there.
    raise HTTPException(status_code=501, detail=f"OAuth flow for {platform} not yet implemented")
