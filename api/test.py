from fastapi import APIRouter, HTTPException
from services import llm as llm_svc

router = APIRouter(prefix="/api/test")


@router.post("/llm", operation_id="testLlm")
def test_llm():
    """Ping Claude Haiku with a minimal prompt to verify the connection."""
    try:
        hint = llm_svc.generate_hint("Reply with exactly: 'Claude is connected.'")
        print("test",hint)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM connection failed: {exc}")
    return {"status": "ok", "response": hint}
