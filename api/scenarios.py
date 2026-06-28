from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.dependencies import get_session
from db.scenarios import ScenariosRepository

router = APIRouter(prefix="/api/scenarios")


@router.get("", operation_id="listScenarios")
def list_scenarios(session: Session = Depends(get_session)):
    return ScenariosRepository(session).get_all()


@router.get("/{scenario_id}", operation_id="getScenario")
def get_scenario(scenario_id: str, session: Session = Depends(get_session)):
    scenario = ScenariosRepository(session).get_by_id(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario
