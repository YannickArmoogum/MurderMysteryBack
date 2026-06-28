"""Prompt templates package."""
from prompts.prompts import (
    PromptBuilder,
    mystery_system_prompt,
    skeleton_system_prompt,
    dossier_system_prompt,
    blueprint_context_message,
    dossier_user_message,
    user_guide_system_prompt,
    user_guide_user_message,
    character_image_prompt,
    narration_prompt,
    hint_prompt,
)

__all__ = [
    "PromptBuilder",
    "mystery_system_prompt",
    "skeleton_system_prompt",
    "dossier_system_prompt",
    "blueprint_context_message",
    "dossier_user_message",
    "user_guide_system_prompt",
    "user_guide_user_message",
    "character_image_prompt",
    "narration_prompt",
    "hint_prompt",
]
