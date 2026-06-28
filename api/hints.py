import asyncio

from fastapi import APIRouter, HTTPException

from prompts import hint_prompt
from services import llm as llm_svc

router = APIRouter(prefix="/api")


@router.post("/hint", operation_id="generateHint")
async def generate_hint(payload: dict):
    """Generate an in-character hint for a player.

    Body: { characterName, suspectName, clue, act }
    """
    prompt = hint_prompt(
        character_name=payload.get("characterName", ""),
        suspect_name=payload.get("suspectName", ""),
        clue=payload.get("clue", ""),
        act=payload.get("act", 1),
    )
    try:
        hint = await asyncio.get_event_loop().run_in_executor(
            None, llm_svc.generate_hint, prompt
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM hint error: {exc}")
    return {"hint": hint}
