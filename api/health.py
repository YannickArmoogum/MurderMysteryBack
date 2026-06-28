from fastapi import APIRouter
from core.config import config

router = APIRouter()


@router.get("/api/health", operation_id="health")
def health():
    return {"status": "ok", "models": {
        "llm": config.LLM_MODEL,
        "image": config.IMAGE_MODEL,
        "tts": config.TTS_MODEL,
    }}
