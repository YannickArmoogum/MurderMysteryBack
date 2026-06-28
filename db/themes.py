"""Themes repository — ORM access, no raw SQL."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Theme


class ThemesRepository:
    UPDATABLE = {"label", "era", "icon", "setting", "icon_image_url"}

    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> list[Theme]:
        return list(self.session.scalars(select(Theme).order_by(Theme.id)))

    def get_by_id(self, theme_id: str) -> Theme | None:
        return self.session.get(Theme, theme_id)

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