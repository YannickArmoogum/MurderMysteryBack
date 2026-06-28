"""Scenarios repository — read-only ORM access, no raw SQL."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Scenario


class ScenariosRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> list[Scenario]:
        return list(self.session.scalars(select(Scenario).order_by(Scenario.id)))

    def get_by_id(self, scenario_id: str) -> Scenario | None:
        return self.session.get(Scenario, scenario_id)