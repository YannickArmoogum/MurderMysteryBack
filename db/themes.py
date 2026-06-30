"""Themes repository — ORM access, no raw SQL."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Theme


class ThemesRepository:
    UPDATABLE = {
        "label", "era", "icon", "setting", "icon_image_url",
        "label_fr", "era_fr", "setting_fr",
    }

    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> list[Theme]:
        return list(self.session.scalars(select(Theme).order_by(Theme.id)))

    def get_by_id(self, theme_id: str) -> Theme | None:
        return self.session.get(Theme, theme_id)

    @staticmethod
    def localize(theme: Theme, language: str = "en") -> dict:
        """Serialize a theme, swapping in French fields when language='fr' (and present)."""
        fr = (language or "en").lower() == "fr"
        return {
            "id": theme.id,
            "label": theme.label_fr if fr and theme.label_fr else theme.label,
            "era": theme.era_fr if fr and theme.era_fr else theme.era,
            "icon": theme.icon,
            "setting": theme.setting_fr if fr and theme.setting_fr else theme.setting,
            "icon_image_url": theme.icon_image_url,
        }

    def list_localized(self, language: str = "en") -> list[dict]:
        return [self.localize(t, language) for t in self.get_all()]

    def get_localized(self, theme_id: str, language: str = "en") -> dict | None:
        theme = self.get_by_id(theme_id)
        return self.localize(theme, language) if theme else None

    def create(self, theme_id: str, label: str, era: str = "",
               icon: str = "🎭", setting: str = "") -> Theme:
        theme = Theme(id=theme_id, label=label, era=era, icon=icon, setting=setting)
        self.session.add(theme)
        self.session.commit()
        self.session.refresh(theme)
        return theme

    def update(self, theme_id: str, **fields) -> Theme | None:
        theme = self.session.get(Theme, theme_id)
        if theme is None:
            return None
        for key, value in fields.items():
            if key in self.UPDATABLE and value is not None:
                setattr(theme, key, value)
        self.session.commit()
        self.session.refresh(theme)
        return theme

    def delete(self, theme_id: str) -> bool:
        theme = self.session.get(Theme, theme_id)
        if theme is None:
            return False
        self.session.delete(theme)
        self.session.commit()
        return True

    def set_icon_image(self, theme_id: str, image_url: str) -> Theme | None:
        return self.update(theme_id, icon_image_url=image_url)