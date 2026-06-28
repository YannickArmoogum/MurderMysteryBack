"""Read-only access to difficulty and tone options."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Difficulty, Tone


class OptionsRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_difficulties(self) -> list[Difficulty]:
        return list(self.session.scalars(select(Difficulty).order_by(Difficulty.id)))

    def get_difficulty_by_id(self,id) -> Difficulty:
        return self.session.scalar(select(Difficulty).where(Difficulty.id ==id))

    def get_tones(self) -> list[Tone]:
        return list(self.session.scalars(select(Tone).order_by(Tone.id)))

    def get_tone_by_id(self, id: str) -> Tone | None:
        return self.session.scalar(select(Tone).where(Tone.id == id))