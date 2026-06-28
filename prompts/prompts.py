"""Prompt templates for the murder mystery generator."""
import json
from pathlib import Path
from sqlalchemy.orm import Session

from db.options import OptionsRepository
from db.themes import ThemesRepository

_DIR = Path(__file__).parent
_MYSTERY_SCHEMA = (_DIR / "mystery_schema.txt").read_text(encoding="utf-8")
_SKELETON_SCHEMA = (_DIR / "mystery_skeleton_schema.txt").read_text(encoding="utf-8")
_DOSSIER_SCHEMA = (_DIR / "character_dossier_schema.txt").read_text(encoding="utf-8")
_GUIDE_SYSTEM = (_DIR / "guide_system.txt").read_text(encoding="utf-8")



class PromptBuilder:
    """Builds LLM prompts, resolving difficulty/tone/theme descriptions from the DB."""

    def __init__(self, session: Session):
        self._opts = OptionsRepository(session)
        self._themes = ThemesRepository(session)

    def theme_info(self, theme_id: str) -> tuple[str, str]:
        """Return (theme_name, setting) for the given theme id."""
        theme = self._themes.get_by_id(theme_id)
        return (theme.label, theme.setting) if theme else ("Custom Theme", "An Elegant Venue")

    def mystery_user_message(
        self,
        theme_id: str,
        player_count: int,
        difficulty_id: str,
        tone_id: str,
    ) -> str:
        theme_name, setting = self.theme_info(theme_id)
        difficulty = self._opts.get_difficulty_by_id(difficulty_id)
        tone = self._opts.get_tone_by_id(tone_id)
        difficulty_note = difficulty.description if difficulty else difficulty_id
        tone_note = tone.description if tone else tone_id
        min_evidence = max(6, player_count)
        return (
            f"Generate a complete murder mystery for exactly {player_count} players.\n"
            f"THEME: {theme_name}\n"
            f"SETTING: {setting}\n"
            f"DIFFICULTY: {difficulty_id} — {difficulty_note}\n"
            f"TONE: {tone_id} — {tone_note}\n"
            f"Generate exactly {player_count} characters. "
            f"Include at least {min_evidence} evidence cards across all 3 acts."
        )


# ── Static prompt functions (no DB dependency) ───────────────────────────────

def mystery_system_prompt() -> str:
    return _MYSTERY_SCHEMA


def skeleton_system_prompt() -> str:
    """Static system prompt for stage-1 blueprint generation (cacheable)."""
    return _SKELETON_SCHEMA


def dossier_system_prompt() -> str:
    """Static system prompt for stage-2 per-character dossier generation (cacheable)."""
    return _DOSSIER_SCHEMA


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


def dossier_user_message(character: dict) -> str:
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
