from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.dependencies import get_session
from db.options import OptionsRepository

router = APIRouter(prefix="/api")


@router.get("/difficulties", operation_id="getDifficulties")
def get_difficulties(session: Session = Depends(get_session)):
    return OptionsRepository(session).get_difficulties()


@router.get("/tones", operation_id="getTones")
def get_tones(session: Session = Depends(get_session)):
    return OptionsRepository(session).get_tones()