"""Prompt templates for the murder mystery generator."""
import json
from pathlib import Path
from sqlalchemy.orm import Session

from db.options import OptionsRepository
from db.themes import ThemesRepository

_DIR = Path(__file__).parent
_MYSTERY_SCHEMA = (_DIR / "mystery_schema.txt").read_text(encoding="utf-8")
_SKELETON_SCHEMA = (_DIR / "mystery_skeleton_schema.txt").read_text(encoding="utf-8")
_CORE_SCHEMA = (_DIR / "core_blueprint_schema.txt").read_text(encoding="utf-8")
_PRODUCTION_SCHEMA = (_DIR / "production_schema.txt").read_text(encoding="utf-8")
_DOSSIER_SCHEMA = (_DIR / "character_dossier_schema.txt").read_text(encoding="utf-8")
_GUIDE_SYSTEM = (_DIR / "guide_system.txt").read_text(encoding="utf-8")


# JSON Schema for the per-character dossier (structured outputs). Constraining the
# response to this shape guarantees valid JSON — no markdown fences, no truncated
# parse failures that would silently drop a character's rich fields.
_STR = {"type": "string"}
_STR_LIST = {"type": "array", "items": {"type": "string"}}
DOSSIER_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "publicIdentity": _STR,
        "secretBackground": _STR,
        "hiddenMotive": _STR,
        "personalObjective": _STR,
        "incriminatingClues": _STR_LIST,
        "exculpatoryClues": _STR_LIST,
        "alibi": _STR,
        "secretOnlyTheyKnow": _STR,
        "behaviouralGuideline": _STR,
        "samplePhrases": _STR_LIST,
        "symbolicDetail": _STR,
    },
    "required": [
        "publicIdentity", "secretBackground", "hiddenMotive", "personalObjective",
        "incriminatingClues", "exculpatoryClues", "alibi", "secretOnlyTheyKnow",
        "behaviouralGuideline", "samplePhrases", "symbolicDetail",
    ],
    "additionalProperties": False,
}



_LANGUAGE_NAMES = {"en": "English", "fr": "French"}


def language_directive(language: str | None) -> str:
    """Instruction appended to generation prompts so all player-facing text is
    written in the requested language. English is the default and adds nothing.

    The JSON keys must stay exactly as specified (English) — only string VALUES
    are translated — because the frontend reads the response by key.
    """
    lang = (language or "en").lower()
    if lang == "en":
        return ""
    name = _LANGUAGE_NAMES.get(lang, "English")
    return (
        f"\n\nIMPORTANT — LANGUAGE: Write ALL player-facing content "
        f"(title, tagline, names, descriptions, clues, dialogue, dossiers, GM notes, "
        f"timeline events and the reveal script) in {name}. "
        f"Keep every JSON key exactly as specified in English; translate only the string values."
    )


class PromptBuilder:
    """Builds LLM prompts, resolving difficulty/tone/theme descriptions from the DB."""

    def __init__(self, session: Session):
        self._opts = OptionsRepository(session)
        self._themes = ThemesRepository(session)

    def theme_info(self, theme_id: str, language: str = "en") -> tuple[str, str]:
        """Return (theme_name, setting) for the given theme id, localized by language."""
        theme = self._themes.get_by_id(theme_id)
        if not theme:
            return ("Custom Theme", "An Elegant Venue")
        loc = self._themes.localize(theme, language)
        return (loc["label"], loc["setting"])

    def mystery_user_message(
        self,
        theme_id: str,
        player_count: int,
        difficulty_id: str,
        tone_id: str,
        language: str = "en",
    ) -> str:
        fr = (language or "en").lower() == "fr"
        theme_name, setting = self.theme_info(theme_id, language)
        difficulty = self._opts.get_difficulty_by_id(difficulty_id)
        tone = self._opts.get_tone_by_id(tone_id)
        difficulty_note = (
            (difficulty.description_fr if fr and difficulty.description_fr else difficulty.description)
            if difficulty else difficulty_id
        )
        tone_note = (
            (tone.description_fr if fr and tone.description_fr else tone.description)
            if tone else tone_id
        )
        min_evidence = max(6, player_count)
        return (
            f"Generate a complete murder mystery for exactly {player_count} players.\n"
            f"THEME: {theme_name}\n"
            f"SETTING: {setting}\n"
            f"DIFFICULTY: {difficulty_id} — {difficulty_note}\n"
            f"TONE: {tone_id} — {tone_note}\n"
            f"Generate exactly {player_count} characters. "
            f"Include at least {min_evidence} evidence cards across all 3 acts."
            + language_directive(language)
        )


# ── Static prompt functions (no DB dependency) ───────────────────────────────

def mystery_system_prompt() -> str:
    return _MYSTERY_SCHEMA


def skeleton_system_prompt() -> str:
    """Static system prompt for stage-1 blueprint generation (cacheable)."""
    return _SKELETON_SCHEMA


def core_blueprint_system_prompt() -> str:
    """Static system prompt for the core blueprint (facts + character skeletons)."""
    return _CORE_SCHEMA


def production_system_prompt() -> str:
    """Static system prompt for acts/evidence/GM-guide/reveal generation (cacheable)."""
    return _PRODUCTION_SCHEMA


def _production_context(core: dict) -> dict:
    """Canonical facts + full cast skeletons handed to the production pass.

    Includes each character's brief (the reveal/evidence writer needs the killer's
    motive and the timeline to stay consistent).
    """
    return {
        "title": core.get("title"),
        "themeName": core.get("themeName"),
        "setting": core.get("setting"),
        "victim": core.get("victim"),
        "murderMethod": core.get("murderMethod"),
        "storyOverview": core.get("storyOverview"),
        "timeline": core.get("timeline", []),
        "characters": [
            {
                "name": c.get("name"),
                "role": c.get("role"),
                "isKiller": bool(c.get("isKiller", False)),
                "relationships": c.get("relationships", []),
                "brief": c.get("brief", ""),
            }
            for c in core.get("characters", [])
        ],
    }


def production_user_message(core: dict, min_evidence: int, language: str = "en") -> str:
    """Per-mystery instruction for the production pass: write structure from the facts."""
    return (
        "CORE BLUEPRINT (binding canonical facts — do not contradict):\n"
        f"{json.dumps(_production_context(core), ensure_ascii=False)}\n\n"
        f"Write the acts, evidence (at least {min_evidence} cards across all 3 acts), "
        "GM guide, and reveal script for this mystery."
        + language_directive(language)
    )


def dossier_system_prompt() -> str:
    """Static system prompt for stage-2 per-character dossier generation (cacheable)."""
    return _DOSSIER_SCHEMA


# ── Single-field revision (edit-by-AI) ────────────────────────────────────────

def field_revision_system_prompt() -> str:
    """Cacheable system prompt for re-prompting one field of existing content."""
    return (
        "You revise a SINGLE field of already-written murder-mystery content on request.\n"
        "Rules:\n"
        "- Rewrite ONLY the requested field. Never invent or alter any other field.\n"
        "- Stay strictly consistent with the surrounding context (names, roles, the "
        "killer's identity, established facts and the mystery's tone).\n"
        "- Match the length, register and point of view of the original field.\n"
        "- Respond with ONLY valid JSON of the form {\"value\": <new value>} — no markdown, "
        "no commentary. If the field is a list, \"value\" is an array of strings; otherwise a string."
    )


def regenerate_field_user_message(
    field: str, context: dict, guidance: str | None, language: str, is_list: bool
) -> str:
    expected = "an array of strings" if is_list else "a single string"
    instruction = (
        f"AUTHOR INSTRUCTION (apply this): {guidance}"
        if guidance and guidance.strip()
        else "Produce a fresh alternative that still fits the context."
    )
    return (
        f"FIELD TO REWRITE: {field}\n"
        f"EXPECTED VALUE TYPE: {expected}\n\n"
        "SURROUNDING CONTEXT (canonical — do not contradict):\n"
        f"{json.dumps(context, ensure_ascii=False)}\n\n"
        f"{instruction}\n\n"
        "Return ONLY JSON: {\"value\": ...}"
        + language_directive(language)
    )


def _blueprint_context(skeleton: dict) -> dict:
    """Shared canonical facts handed to every dossier call (cached across characters)."""
    killer_name = next(
        (c.get("name") for c in skeleton.get("characters", []) if c.get("isKiller")),
        "Unknown",
    )
    return {
        "title": skeleton.get("title"),
        "themeName": skeleton.get("themeName"),
        "setting": skeleton.get("setting"),
        "victim": skeleton.get("victim"),
        "murderMethod": skeleton.get("murderMethod"),
        "storyOverview": skeleton.get("storyOverview"),
        "timeline": skeleton.get("timeline", []),
        "killerName": killer_name,
        "cast": [
            {
                "name": c.get("name"),
                "role": c.get("role"),
                "relationships": c.get("relationships", []),
            }
            for c in skeleton.get("characters", [])
        ],
    }


def blueprint_context_message(skeleton: dict) -> str:
    """Cacheable system block: the binding facts shared by all dossier calls."""
    return (
        "MYSTERY BLUEPRINT (binding canonical facts — do not contradict):\n"
        f"{json.dumps(_blueprint_context(skeleton), ensure_ascii=False)}"
    )


def dossier_user_message(character: dict, language: str = "en") -> str:
    """Per-character instruction: which character to expand and their canonical brief."""
    payload = {
        "id": character.get("id"),
        "name": character.get("name"),
        "role": character.get("role"),
        "personalityArchetype": character.get("personalityArchetype"),
        "costume": character.get("costume"),
        "isKiller": bool(character.get("isKiller", False)),
        "relationships": character.get("relationships", []),
        "brief": character.get("brief", ""),
    }
    killer_note = (
        "This character IS the killer — write the dossier so a sharp player could "
        "eventually unmask them, but never make it obvious."
        if payload["isKiller"]
        else "This character is NOT the killer, but must still read as a credible suspect."
    )
    return (
        f"Write the full dossier for this character:\n{json.dumps(payload, ensure_ascii=False)}\n\n"
        f"{killer_note}"
        + language_directive(language)
    )


def user_guide_system_prompt() -> str:
    return _GUIDE_SYSTEM


def user_guide_user_message(mystery: dict) -> str:
    killer_name = next(
        (c["name"] for c in mystery.get("characters", []) if c.get("isKiller")),
        "Unknown"
    )
    killer_motive = next(
        (c.get("hiddenMotive", "") for c in mystery.get("characters", []) if c.get("isKiller")),
        ""
    )
    payload = {
        "title": mystery.get("title"),
        "tagline": mystery.get("tagline"),
        "themeName": mystery.get("themeName"),
        "setting": mystery.get("setting"),
        "tone": mystery.get("tone"),
        "playerCount": mystery.get("playerCount"),
        "victim": mystery.get("victim"),
        "murderMethod": mystery.get("murderMethod"),
        "characters": [
            {
                "name": c["name"],
                "role": c["role"],
                "publicIdentity": c.get("publicIdentity", ""),
                "costume": c.get("costume", ""),
            }
            for c in mystery.get("characters", [])
        ],
        "evidence": [
            {
                "name": e["name"],
                "revealedInAct": e.get("revealedInAct", 1),
                "actsAs": e.get("actsAs", ""),
            }
            for e in mystery.get("evidence", [])
        ],
        "acts": [
            {
                "number": a["number"],
                "title": a["title"],
                "duration": a.get("duration", ""),
                "keyEvents": a.get("keyEvents", []),
                "cluesReleased": a.get("cluesReleased", []),
                "gmNotes": a.get("gmNotes", ""),
            }
            for a in mystery.get("acts", [])
        ],
        "killer": {"name": killer_name, "motive": killer_motive},
        "revealScript": mystery.get("revealScript", {}),
    }
    return f"Write the invitation text and GM script for this mystery:\n{json.dumps(payload, ensure_ascii=False)}"


def character_image_prompt(name: str, role: str, costume: str, theme_name: str) -> str:
    return (
        f"Portrait of {name}, {role} at a {theme_name} event. "
        f"Wearing: {costume}. "
        "Cinematic lighting, dramatic shadows, painterly style, elegant composition, "
        "character portrait, mysterious atmosphere, high detail, 8k."
    )


def narration_prompt(text: str) -> str:
    return f"[dramatic narrator voice] {text} [pause]"


def hint_prompt(character_name: str, suspect_name: str, clue: str, act: int) -> str:
    return (
        f"You are a murder mystery game master whispering a hint to a player. Be atmospheric and brief.\n\n"
        f"The player controls character: {character_name}\n"
        f"The suspect they are watching: {suspect_name}\n"
        f"A clue they just discovered: {clue}\n"
        f"Current act: {act}\n\n"
        "Write a 2-sentence in-character whisper hint that helps the player interpret this clue "
        "without giving away the answer. Be evocative and mysterious. Output ONLY the hint text."
    )
