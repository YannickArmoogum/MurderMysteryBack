import asyncio

from fastapi import APIRouter, HTTPException

from core.schemas.schemas import CustomizeRequest, CustomizeResponse
from services import claude as claude_svc

router = APIRouter(prefix="/api")


@router.post("/customize", response_model=CustomizeResponse, operation_id="customizeMystery")
async def customize_mystery(req: CustomizeRequest):
    """Claude-powered chatbot for surface-level mystery customization."""
    try:
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: claude_svc.customize_mystery(
                req.message,
                req.mysterySummary,
                [h.model_dump() for h in req.chatHistory],
            ),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Claude error: {exc}")
    return CustomizeResponse(
        response=result.get("response", ""),
        changes=result.get("changes"),
        refused=result.get("refused", False),
    )
