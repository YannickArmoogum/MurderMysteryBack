"""App settings repository — key/value ORM access, no raw SQL."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Setting


class SettingsRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> list[Setting]:
        return list(self.session.scalars(select(Setting).order_by(Setting.key)))

    def get(self, key: str) -> str | None:
        setting = self.session.get(Setting, key)
        return setting.value if setting else None

    def set_value(self, key: str, value: str) -> Setting:
        setting = self.session.get(Setting, key)
        if setting is None:
            setting = Setting(key=key, value=value)
            self.session.add(setting)
        else:
            setting.value = value
        self.session.commit()
        self.session.refresh(setting)
        return setting