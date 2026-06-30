from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.dependencies import get_session
from db.options import OptionsRepository

router = APIRouter(prefix="/api")


@router.get("/difficulties", operation_id="getDifficulties")
def get_difficulties(lang: str = "en", session: Session = Depends(get_session)):
    return OptionsRepository(session).list_difficulties_localized(lang)


@router.get("/tones", operation_id="getTones")
def get_tones(lang: str = "en", session: Session = Depends(get_session)):
    return OptionsRepository(session).list_tones_localized(lang)