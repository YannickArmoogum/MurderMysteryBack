from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.dependencies import get_session
from db.settings import SettingsRepository

router = APIRouter(prefix="/api/settings")


@router.get("", operation_id="getSettings")
def get_settings(session: Session = Depends(get_session)):
    return SettingsRepository(session).get_all()


@router.put("/{key}", operation_id="updateSetting")
def update_setting(key: str, body: dict, session: Session = Depends(get_session)):
    value = body.get("value")
    if value is None:
        raise HTTPException(status_code=422, detail="'value' is required")
    return SettingsRepository(session).set_value(key, str(value))