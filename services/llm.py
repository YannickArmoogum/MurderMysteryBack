"""Claude Haiku text generation with prompt caching for minimal API cost."""
import json
import re

from core.config.config import CLAUDE_LLM_MODEL, CLAUDE_PROSE_MODEL
from db.dependencies import get_anthropic_client
from prompts import (
    mystery_system_prompt,
    skeleton_system_prompt,
    dossier_system_prompt,
    blueprint_context_message,
    dossier_user_message,
    user_guide_system_prompt,
    user_guide_user_message,
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
    print(response)
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


def generate_character_dossier(skeleton: dict, character: dict) -> dict:
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
    with client.messages.stream(
        model=CLAUDE_LLM_MODEL,
        max_tokens=4000,
        system=system_blocks,
        messages=[{"role": "user", "content": dossier_user_message(character)}],
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
    print("response",response)
    raw = response.content[0].text
    return _extract_json(raw)


def generate_hint(prompt: str) -> str:
    """Generate a short in-game hint. Uses Haiku with tight token budget."""
    client = get_anthropic_client()

    response = client.messages.create(
        model=CLAUDE_LLM_MODEL,
        max_tokens=150,
        messages=[{"role":"user","content":prompt}]
    )
    return response.content[0].text.strip()
