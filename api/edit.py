import asyncio

from fastapi import APIRouter, HTTPException

from core.schemas.schemas import RegenerateFieldRequest, RegenerateFieldResponse
from services import llm as llm_svc

router = APIRouter(prefix="/api")


@router.post("/regenerate-field", response_model=RegenerateFieldResponse, operation_id="regenerateField")
async def regenerate_field(req: RegenerateFieldRequest):
    """Re-prompt the AI to rewrite a single field of already-generated content.

    The client sends the field name, the surrounding context (e.g. the character
    dossier) and an optional author instruction; the model returns just that field.
    """
    try:
        value = await asyncio.get_event_loop().run_in_executor(
            None, llm_svc.regenerate_field, req.field, req.context, req.guidance, req.language
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Field regeneration error: {exc}")
    return RegenerateFieldResponse(field=req.field, value=value)
