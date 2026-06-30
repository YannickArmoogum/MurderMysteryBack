"""Email-gated share links for individual character cards."""
import json
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.schemas.schemas import (
    CreateShareRequest,
    CreateShareResponse,
    ShareInfoResponse,
    UnlockShareRequest,
    ShareCardResponse,
)
from db.dependencies import get_session
from db.models import CardShare

router = APIRouter(prefix="/api")


@router.post("/shares", response_model=CreateShareResponse, operation_id="createShare")
async def create_share(req: CreateShareRequest, session: Session = Depends(get_session)):
    """Host creates an email-gated link for one character's card."""
    email = req.email.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=400, detail="A valid email is required.")

    token = secrets.token_urlsafe(9)
    share = CardShare(
        token=token,
        email=email,
        participant_name=req.participantName.strip(),
        mystery_title=req.mysteryTitle,
        character_json=json.dumps(req.character, ensure_ascii=False),
        timeline_json=json.dumps(req.timeline, ensure_ascii=False),
        portrait_url=req.portraitUrl,
        language=req.language,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    session.add(share)
    session.commit()
    return CreateShareResponse(token=token)


@router.get("/shares/{token}", response_model=ShareInfoResponse, operation_id="getShareInfo")
async def get_share_info(token: str, session: Session = Depends(get_session)):
    """Public, non-sensitive info for the locked page (no card content)."""
    share = session.get(CardShare, token)
    if not share:
        raise HTTPException(status_code=404, detail="This link is invalid or has expired.")
    return ShareInfoResponse(mysteryTitle=share.mystery_title, language=share.language, locked=True)


@router.post("/shares/{token}/unlock", response_model=ShareCardResponse, operation_id="unlockShare")
async def unlock_share(token: str, req: UnlockShareRequest, session: Session = Depends(get_session)):
    """Return the card only if the supplied email matches the assigned one."""
    share = session.get(CardShare, token)
    if not share:
        raise HTTPException(status_code=404, detail="This link is invalid or has expired.")
    if req.email.strip().lower() != share.email:
        raise HTTPException(status_code=403, detail="That email doesn't match this invitation.")
    return ShareCardResponse(
        participantName=share.participant_name,
        mysteryTitle=share.mystery_title,
        character=json.loads(share.character_json),
        timeline=json.loads(share.timeline_json),
        portraitUrl=share.portrait_url,
        language=share.language,
    )
