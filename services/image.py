"""
Character portrait generation via Pollinations.ai — completely free, no API key.
Falls back to HF FLUX.1-schnell if pollinations is unavailable.
"""
import base64
import io
import urllib.parse
from huggingface_hub import InferenceClient
import urllib.request
from core.config.config import HF_TOKEN, IMAGE_MODEL

_POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"


def _generate_via_pollinations(prompt: str) -> str:
    """
    Call pollinations.ai — free, no auth, no quota.
    Returns a base64 data URI (image/jpeg).
    """
    encoded = urllib.parse.quote(prompt, safe="")
    url = (
        f"{_POLLINATIONS_BASE}/{encoded}"
        "?width=512&height=512&nologo=true&model=flux-schnell&seed=-1"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "MurderMysteryApp/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        image_bytes = resp.read()
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def _generate_via_hf_flux(prompt: str) -> str:
    """HF FLUX.1-schnell fallback (requires HF_TOKEN)."""
    client = InferenceClient(token=HF_TOKEN)
    image = client.text_to_image(prompt, model=IMAGE_MODEL, width=512, height=512)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def generate_character_portrait(prompt: str) -> str:
    """
    Generate a character portrait.
    Tries pollinations.ai first (free); falls back to HF FLUX on error.
    """
    try:
        return _generate_via_pollinations(prompt)
    except Exception:
        return _generate_via_hf_flux(prompt)
