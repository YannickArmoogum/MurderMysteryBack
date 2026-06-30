"""Claude Haiku text generation with prompt caching for minimal API cost."""
import json
import re

from core.config.config import CLAUDE_LLM_MODEL, CLAUDE_PROSE_MODEL
from db.dependencies import get_anthropic_client
from prompts import (
    mystery_system_prompt,
    skeleton_system_prompt,
    core_blueprint_system_prompt,
    production_system_prompt,
    production_user_message,
    dossier_system_prompt,
    blueprint_context_message,
    dossier_user_message,
    field_revision_system_prompt,
    regenerate_field_user_message,
    user_guide_system_prompt,
    user_guide_user_message,
    DOSSIER_JSON_SCHEMA,
)




def _extract_json(raw: str) -> dict:
    """Extract the first JSON object from a raw LLM response."""
    text = raw.strip()

    # Strip opening fence (model may omit the closing fence on truncated output)
    text = re.sub(r"^```(?:json)?\s*", "", text).strip()
    # Strip closing fence if present
    text = re.sub(r"\s*```\s*$", "", text).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find the outermost {...} block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"No valid JSON found in LLM response. Raw (first 500 chars): {raw[:500]}")


def generate_mystery_json(user_msg: str) -> dict:
    """Call Claude and return a parsed mystery dict. Uses prompt caching on the static schema."""
    claude_client = get_anthropic_client()
    system_blocks = [
        {
            "type": "text",
            "text": mystery_system_prompt(),
            "cache_control": {"type": "ephemeral"},
        }
    ]
    # Stream: verbose multi-character mysteries can run long, and streaming avoids
    # the SDK's HTTP timeout guard that trips on large max_tokens. Haiku 4.5 allows
    # up to 64K output tokens; 32K leaves ample headroom for a full 14-player dossier.
    with claude_client.messages.stream(
        model=CLAUDE_LLM_MODEL,
        max_tokens=32000,
        system=system_blocks,
        messages=[{"role": "user", "content": user_msg}],
    ) as stream:
        response = stream.get_final_message()

    if response.stop_reason == "max_tokens":
        print("WARNING: mystery generation hit max_tokens — output may be truncated.")
    return _extract_json(response.content[0].text)


def generate_core_blueprint(user_msg: str) -> dict:
    """Stage 1a: generate only the core facts + thin character skeletons.

    This is the critical-path call — it gates the per-character dossier fan-out.
    Keeping it small (no acts/evidence/GM-guide/reveal) means dossiers start sooner;
    the heavier structural content is generated in parallel (see generate_production).
    """
    client = get_anthropic_client()
    system_blocks = [
        {
            "type": "text",
            "text": core_blueprint_system_prompt(),
            "cache_control": {"type": "ephemeral"},
        }
    ]
    with client.messages.stream(
        model=CLAUDE_LLM_MODEL,
        max_tokens=4000,
        system=system_blocks,
        messages=[{"role": "user", "content": user_msg}],
    ) as stream:
        response = stream.get_final_message()

    if response.stop_reason == "max_tokens":
        print("WARNING: core blueprint hit max_tokens — output may be truncated.")
    return _extract_json(response.content[0].text)


def generate_production(core: dict, language: str = "en") -> dict:
    """Stage 1b: acts + evidence + GM guide + reveal script, derived from the core facts.

    Runs concurrently with the dossier fan-out (it needs the core blueprint, but the
    dossiers don't need it), so its output stays off the critical path.
    """
    client = get_anthropic_client()
    char_count = len(core.get("characters") or [])
    min_evidence = max(6, char_count)
    system_blocks = [
        {
            "type": "text",
            "text": production_system_prompt(),
            "cache_control": {"type": "ephemeral"},
        }
    ]
    with client.messages.stream(
        model=CLAUDE_LLM_MODEL,
        max_tokens=8000,
        system=system_blocks,
        messages=[{"role": "user", "content": production_user_message(core, min_evidence, language)}],
    ) as stream:
        response = stream.get_final_message()

    if response.stop_reason == "max_tokens":
        print("WARNING: production generation hit max_tokens — output may be truncated.")
    return _extract_json(response.content[0].text)


def generate_mystery_skeleton(user_msg: str) -> dict:
    """Stage 1: generate the mystery blueprint (facts + structure + character skeletons).

    Much smaller output than the monolithic prompt, so it returns quickly and
    establishes the canonical truth the parallel dossier pass must honour.
    """
    client = get_anthropic_client()
    system_blocks = [
        {
            "type": "text",
            "text": skeleton_system_prompt(),
            "cache_control": {"type": "ephemeral"},
        }
    ]
    with client.messages.stream(
        model=CLAUDE_LLM_MODEL,
        max_tokens=8000,
        system=system_blocks,
        messages=[{"role": "user", "content": user_msg}],
    ) as stream:
        response = stream.get_final_message()

    if response.stop_reason == "max_tokens":
        print("WARNING: skeleton generation hit max_tokens — output may be truncated.")
    return _extract_json(response.content[0].text)


def generate_character_dossier(skeleton: dict, character: dict, language: str = "en") -> dict:
    """Stage 2: expand a single character into a full dossier.

    Called once per character (in parallel). The static dossier schema and the
    shared blueprint context are sent as cached system blocks, so every call
    after the first reuses the cache for ~90% input-token savings.
    """
    client = get_anthropic_client()
    system_blocks = [
        {
            "type": "text",
            "text": dossier_system_prompt(),
            "cache_control": {"type": "ephemeral"},
        },
        {
            "type": "text",
            "text": blueprint_context_message(skeleton),
            "cache_control": {"type": "ephemeral"},
        },
    ]
    # Structured outputs: constrain the response to the dossier schema so it is
    # always valid JSON. Avoids markdown fences and the parse failures that would
    # otherwise silently drop a character's rich fields. 6K tokens headroom keeps a
    # verbose dossier from truncating (which breaks the JSON even when constrained).
    with client.messages.stream(
        model=CLAUDE_LLM_MODEL,
        max_tokens=6000,
        system=system_blocks,
        messages=[{"role": "user", "content": dossier_user_message(character, language)}],
        output_config={"format": {"type": "json_schema", "schema": DOSSIER_JSON_SCHEMA}},
    ) as stream:
        response = stream.get_final_message()

    if response.stop_reason == "max_tokens":
        print(f"WARNING: dossier for {character.get('name')} hit max_tokens — may be truncated.")
    return _extract_json(response.content[0].text)


def generate_user_guide(mystery_data: dict) -> dict:
    """
    Generate invitation text + GM running script for a mystery.
    Returns {"invitationText": str, "gmScript": str (markdown)}.
    Uses a cached system prompt for ~90 % cost savings on repeat calls.
    """
    client = get_anthropic_client()
    system_blocks = [
        {
            "type": "text",
            "text": user_guide_system_prompt(),
            "cache_control": {"type": "ephemeral"},
        }
    ]
    user_msg = user_guide_user_message(mystery_data)
    response = client.messages.create(
        model=CLAUDE_PROSE_MODEL,
        max_tokens=8192,
        system=system_blocks,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = response.content[0].text
    return _extract_json(raw)


def regenerate_field(field: str, context: dict, guidance: str | None = None, language: str = "en"):
    """Rewrite one field of existing content (edit-by-AI). Returns a str or list[str]
    matching the original field's type. Uses a cached system prompt for cost savings."""
    client = get_anthropic_client()
    is_list = isinstance(context.get(field), list)
    system_blocks = [
        {
            "type": "text",
            "text": field_revision_system_prompt(),
            "cache_control": {"type": "ephemeral"},
        }
    ]
    response = client.messages.create(
        model=CLAUDE_LLM_MODEL,
        max_tokens=1500,
        system=system_blocks,
        messages=[{"role": "user", "content": regenerate_field_user_message(field, context, guidance, language, is_list)}],
    )
    data = _extract_json(response.content[0].text)
    value = data.get("value")
    # Coerce to the original field's shape so the client always gets what it expects.
    if is_list and not isinstance(value, list):
        value = [] if value is None else [str(value)]
    if not is_list and isinstance(value, list):
        value = " ".join(str(v) for v in value)
    return value


def generate_hint(prompt: str) -> str:
    """Generate a short in-game hint. Uses Haiku with tight token budget."""
    client = get_anthropic_client()

    response = client.messages.create(
        model=CLAUDE_LLM_MODEL,
        max_tokens=150,
        messages=[{"role":"user","content":prompt}]
    )
    return response.content[0].text.strip()
