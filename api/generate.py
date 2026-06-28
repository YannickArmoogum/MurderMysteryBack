import asyncio

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.schemas.schemas import GenerateRequest, UserGuideRequest, UserGuideResponse
from services.mystery import mystery_stream_generator, assemble_mystery, generate_mystery_raw
from services import llm as llm_svc
from db.dependencies import get_session
from prompts import PromptBuilder

router = APIRouter(prefix="/api")


@router.post("/generate/stream", operation_id="generateStream")
async def generate_stream(req: GenerateRequest, session: Session = Depends(get_session)):
    """Server-Sent Events endpoint — streams progress then the final mystery."""
    return StreamingResponse(mystery_stream_generator(req, session), media_type="text/event-stream")


@router.post("/generate", response_model=dict, operation_id="generate")
async def generate(req: GenerateRequest, session: Session = Depends(get_session)):
    """Non-streaming full generation (no images, no audio)."""
    builder = PromptBuilder(session)
    theme_name, setting = builder.theme_info(req.theme)
    try:
        raw = await generate_mystery_raw(req, session)
    except Exception as exc:
        print(exc)
        raise HTTPException(status_code=502, detail=f"LLM error: {exc}")
    return assemble_mystery(raw, req, theme_name, setting).model_dump()


@router.post("/generate/guide", response_model=UserGuideResponse, operation_id="generateUserGuide")
async def generate_user_guide(req: UserGuideRequest):
    """Generate a player invitation letter + GM running script for a mystery."""
    try:
        result = await asyncio.get_event_loop().run_in_executor(
            None, llm_svc.generate_user_guide, req.mystery
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Guide generation error: {exc}")
    return UserGuideResponse(
        invitationText=result.get("invitationText", ""),
        gmScript=result.get("gmScript", ""),
    )
