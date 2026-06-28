import os
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN: str = os.environ.get("HF_TOKEN", "")
DB_URL: str = os.environ.get("DATABASE_URL")
ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
FRONTEND_URL: str = os.environ.get("FRONTEND_URL", "http://localhost:4200")
PORT: int = int(os.environ.get("PORT", "8000"))

# Model IDs
LLM_MODEL = "NousResearch/Hermes-3-Llama-3.1-8B"  # kept for reference
CLAUDE_LLM_MODEL = "claude-haiku-4-5-20251001"      # fast/cheap: mystery JSON, hints
CLAUDE_PROSE_MODEL = "claude-sonnet-4-6"             # better prose: invitation + GM script
IMAGE_MODEL = "black-forest-labs/FLUX.1-schnell"
TTS_MODEL = "suno/bark"
