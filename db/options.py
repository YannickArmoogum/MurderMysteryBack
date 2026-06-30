"""Read-only access to difficulty and tone options."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Difficulty, Tone


def localize_option(option, language: str = "en") -> dict:
    """Serialize a Difficulty/Tone, swapping in French fields when language='fr'."""
    fr = (language or "en").lower() == "fr"
    return {
        "id": option.id,
        "label": option.label_fr if fr and option.label_fr else option.label,
        "description": option.description_fr if fr and option.description_fr else option.description,
    }


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

    def list_difficulties_localized(self, language: str = "en") -> list[dict]:
        return [localize_option(d, language) for d in self.get_difficulties()]

    def list_tones_localized(self, language: str = "en") -> list[dict]:
        return [localize_option(t, language) for t in self.get_tones()]