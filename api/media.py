import asyncio

from fastapi import APIRouter, HTTPException

from core.schemas.schemas import (
    CharacterImageRequest,
    NarrationRequest,
    CharacterCardRequest,
    CharacterCardResponse,
    ThemeIconRequest,
    ThemeIconResponse,
    DefaultAvatarRequest,
    DefaultAvatarResponse,
)
from prompts import character_image_prompt, narration_prompt
from services import image as image_svc
from services import tts as tts_svc
from services import claude as claude_svc

router = APIRouter(prefix="/api")


@router.post("/generate/character-image", operation_id="generateCharacterImage")
async def character_image(req: CharacterImageRequest):
    prompt = character_image_prompt(req.name, req.role, req.costume, req.themeName)
    try:
        data_uri = await asyncio.get_event_loop().run_in_executor(
            None, image_svc.generate_character_portrait, prompt
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Image generation error: {exc}")
    return {"characterId": req.characterId, "imageUrl": data_uri}


@router.post("/narration", operation_id="generateNarration")
async def narration(req: NarrationRequest):
    text = narration_prompt(req.text)
    try:
        audio = await asyncio.get_event_loop().run_in_executor(
            None, tts_svc.generate_narration, text
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"TTS error: {exc}")
    return {"audioData": audio}


@router.post("/character-card", response_model=CharacterCardResponse, operation_id="generateCharacterCard")
async def generate_character_card(req: CharacterCardRequest):
    """Generate a FLUX portrait adapted to the participant's appearance via Claude Vision."""
    char = req.character
    appearance = ""
    if req.imageBase64:
        try:
            appearance = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: claude_svc.analyze_participant_photo(
                    req.imageBase64, req.imageMediaType or "image/jpeg"
                ),
            )
        except Exception:
            appearance = ""

    costume = char.get("costume", "formal attire")
    role = char.get("role", "guest")
    theme_name = char.get("themeName", "elegant event")
    if appearance:
        prompt = (
            f"Portrait of a person matching this description: {appearance}. "
            f"Wearing: {costume}. "
            f"Setting: {theme_name}. Character role: {role}. "
            "Painterly style, cinematic lighting, dramatic shadows, elegant composition, "
            "mysterious atmosphere, high detail, 8k."
        )
    else:
        prompt = character_image_prompt(char.get("name", "Guest"), role, costume, theme_name)

    try:
        portrait_url = await asyncio.get_event_loop().run_in_executor(
            None, image_svc.generate_character_portrait, prompt
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Portrait generation error: {exc}")

    return CharacterCardResponse(
        portraitUrl=portrait_url,
        participantName=req.participantName,
        characterId=req.characterId,
    )


@router.post("/theme-icon", response_model=ThemeIconResponse, operation_id="generateThemeIcon")
async def generate_theme_icon(req: ThemeIconRequest):
    """Generate a small atmospheric icon image for a murder mystery theme."""
    prompt = (
        f"Dark atmospheric icon for a murder mystery themed '{req.themeName}'. "
        f"Setting: {req.setting}. "
        "Gothic art nouveau style, deep shadows, candlelight, mysterious silhouette, "
        "square composition, icon design, dark background, high contrast, ornate border."
    )
    try:
        image_url = await asyncio.get_event_loop().run_in_executor(
            None, image_svc.generate_character_portrait, prompt
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Icon generation error: {exc}")
    return ThemeIconResponse(themeId=req.themeId, imageUrl=image_url)


@router.post("/default-avatar", response_model=DefaultAvatarResponse, operation_id="generateDefaultAvatar")
async def generate_default_avatar(req: DefaultAvatarRequest):
    """Generate a generic mystery character silhouette for a given role."""
    prompt = (
        f"Elegant character silhouette portrait of a '{req.role}' "
        f"at a {req.themeName} murder mystery event. "
        "Art nouveau style, dark background, gold accents, mysterious atmosphere, "
        "stylized illustration, no face visible, dramatic pose, ornate costume details."
    )
    try:
        image_url = await asyncio.get_event_loop().run_in_executor(
            None, image_svc.generate_character_portrait, prompt
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Avatar generation error: {exc}")
    return DefaultAvatarResponse(imageUrl=image_url)
