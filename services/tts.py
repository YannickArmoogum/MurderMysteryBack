"""Bark TTS narration via HF Inference API."""
import base64
import io
from huggingface_hub import InferenceClient
from core.config.config import HF_TOKEN, TTS_MODEL


_client: InferenceClient | None = None


def _get_client() -> InferenceClient:
    global _client
    if _client is None:
        _client = InferenceClient(token=HF_TOKEN)
    return _client


def generate_narration(text: str) -> str:
    """
    Generate narration audio with Bark.
    Returns a base64-encoded data URI: data:audio/wav;base64,...
    """
    client = _get_client()
    audio = client.text_to_speech(
        text,
        model=TTS_MODEL,
    )
    # audio is bytes (WAV)
    if isinstance(audio, (bytes, bytearray)):
        raw = bytes(audio)
    else:
        buf = io.BytesIO()
        buf.write(audio.read() if hasattr(audio, "read") else audio)
        raw = buf.getvalue()

    b64 = base64.b64encode(raw).decode("utf-8")
    return f"data:audio/wav;base64,{b64}"
