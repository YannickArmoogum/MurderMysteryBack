"""Claude (Anthropic) service — vision analysis + mystery customization chatbot."""
import json
import anthropic
from core.config import config

_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

CLAUDE_VISION_MODEL = "claude-haiku-4-5-20251001"   # vision + chatbot — cheapest with vision
CLAUDE_MODEL = CLAUDE_VISION_MODEL                   # alias kept for compat

ALLOWED_FIELDS = {
    "character": {"name", "costume", "publicIdentity", "behaviouralGuideline", "personalObjective", "relationships"},
    "evidence": {"name", "description"},
}

_CUSTOMIZE_SYSTEM = """You are a murder mystery game customization assistant. The host can tweak surface details but the core mystery must remain intact.

ALLOWED CHANGES — you may only suggest modifications to these fields:
- character: name, costume, publicIdentity, behaviouralGuideline, personalObjective, relationships (wording only)
- evidence: name, description (flavour text only)

ABSOLUTELY FORBIDDEN — refuse any request that touches:
- isKiller (who the murderer is)
- murderMethod, storyOverview, acts, victim identity
- incriminatingClues, exculpatoryClues (breaks game balance)
- secretBackground, hiddenMotive, secretOnlyTheyKnow (reveals solution)
- revealedInAct, actsAs on evidence (breaks clue-release timing)

INTEGRITY RULES:
- Each character must keep at minimum 2 incriminating and 2 exculpatory clues (no deletions)
- Total evidence cards may not drop below 5
- You cannot rename a character to the same name as another character

RESPONSE FORMAT — always reply with valid JSON only, no prose outside the JSON:

If the change is allowed:
{"response": "<friendly 1-2 sentence confirmation explaining what was changed>", "changes": [{"type": "character|evidence", "targetId": "<id>", "field": "<field>", "value": "<new value>"}]}

If the change is forbidden or would break game integrity:
{"response": "<polite 1-2 sentence refusal explaining why, plus one allowed alternative>", "refused": true}

Do not mix allowed and forbidden changes in one response. If a request is partially valid, ask for clarification."""


def analyze_participant_photo(image_base64: str, media_type: str = "image/jpeg") -> str:
    """Use Claude Vision to describe a participant's appearance for portrait generation."""
    response = _client.messages.create(
        model=CLAUDE_VISION_MODEL,
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_base64,
                    },
                },
                {
                    "type": "text",
                    "text": (
                        "Describe this person's physical appearance for a portrait artist in 3-4 concise sentences. "
                        "Include: hair colour, length and style; eye colour; skin tone; approximate age range; "
                        "face shape and any notable features. Be precise and factual."
                    ),
                },
            ],
        }],
    )
    return response.content[0].text.strip()


def customize_mystery(message: str, mystery_summary: dict, chat_history: list[dict]) -> dict:
    """Run the customization chatbot. Returns a dict with response + optional changes."""
    messages: list[dict] = []

    # Inject prior turns (last 10 to cap context)
    for turn in chat_history[-10:]:
        role = turn.get("role", "user")
        if role not in ("user", "assistant"):
            continue
        messages.append({"role": role, "content": turn["content"]})

    # Current user message — inject mystery context on first turn
    context_prefix = ""
    if not chat_history:
        context_prefix = f"Mystery context (do not modify anything not listed as allowed):\n{json.dumps(mystery_summary, ensure_ascii=False)[:3000]}\n\n"

    messages.append({"role": "user", "content": f"{context_prefix}Request: {message}"})

    response = _client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=800,
        system=_CUSTOMIZE_SYSTEM,
        messages=messages,
    )

    raw_text = response.content[0].text.strip()

    # Strip markdown code fences if Claude wraps in ```json ... ```
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        # Fallback: treat as plain response with no changes
        result = {"response": raw_text, "refused": False}

    # Sanitise: remove any changes to forbidden fields
    if "changes" in result and isinstance(result["changes"], list):
        safe_changes = []
        for change in result["changes"]:
            c_type = change.get("type", "")
            c_field = change.get("field", "")
            allowed = ALLOWED_FIELDS.get(c_type, set())
            if c_field in allowed:
                safe_changes.append(change)
        result["changes"] = safe_changes or None

    return result
