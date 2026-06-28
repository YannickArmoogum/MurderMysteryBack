from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Any, List, Literal, Optional
import uuid


# ── Request ─────────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    theme: str
    playerCount: int = Field(ge=6, le=14)
    difficulty: Literal["casual", "challenging", "expert"]
    tone: Literal["dramatic", "dark", "romantic", "satirical"]


class CharacterImageRequest(BaseModel):
    characterId: str
    name: str
    role: str
    costume: str
    theme: str
    themeName: str


class NarrationRequest(BaseModel):
    text: str
    voice_preset: str = "v2/en_speaker_6"  # Bark preset


# ── Response fragments ───────────────────────────────────────────────────────

class Victim(BaseModel):
    name: str
    role: str
    description: str


class GeneratedCharacter(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    role: str
    publicIdentity: str
    secretBackground: str
    personalityArchetype: str
    hiddenMotive: str
    personalObjective: str
    incriminatingClues: list[str]
    exculpatoryClues: list[str]
    alibi: str = ""
    secretOnlyTheyKnow: str
    behaviouralGuideline: str
    samplePhrases: list[str] = Field(default_factory=list)
    symbolicDetail: str = ""
    costume: str
    isKiller: bool
    relationships: list[str]
    imageUrl: Optional[str] = None


class EvidenceCard(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: Literal["physical", "testimony", "document", "behavioral"]
    description: str
    actsAs: str
    revealedInAct: Literal[1, 2, 3]


class TimelineEvent(BaseModel):
    time: str
    event: str


class MysteryAct(BaseModel):
    number: Literal[1, 2, 3]
    title: str
    duration: str
    summary: str
    keyEvents: list[str]
    cluesReleased: list[str]
    gmNotes: str


class GMGuide(BaseModel):
    setupInstructions: list[str]
    roomSetup: list[str]
    lightingAndMusic: str
    costumeNotes: str
    timingBreakdown: list[str]
    managingDominantPlayers: str
    helpingStuckGroups: str
    printableChecklist: list[str]


class RevealScript(BaseModel):
    openingStatement: str
    timelineReconstruction: str
    methodExplanation: str
    motiveReveal: str
    emotionalConclusion: str
    optionalTwist: Optional[str] = None


class GeneratedMystery(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    theme: str
    themeName: str
    setting: str
    difficulty: str
    tone: str
    playerCount: int
    tagline: str
    victim: Victim
    murderMethod: str
    storyOverview: str
    timeline: list[TimelineEvent]
    acts: list[MysteryAct]
    characters: list[GeneratedCharacter]
    evidence: list[EvidenceCard]
    gmGuide: GMGuide
    revealScript: RevealScript
    generatedAt: str


# ── Streaming event ──────────────────────────────────────────────────────────

class GenerationProgress(BaseModel):
    step: str
    message: str
    progress: int  # 0–100


# ── Character Card (participant photo → portrait) ─────────────────────────────

class CharacterCardRequest(BaseModel):
    participantName: str
    characterId: str
    character: dict  # serialised GeneratedCharacter fields
    imageBase64: Optional[str] = None        # base64-encoded image data (no prefix)
    imageMediaType: Optional[str] = "image/jpeg"


class CharacterCardResponse(BaseModel):
    portraitUrl: str        # base64 data URI  data:image/png;base64,...
    participantName: str
    characterId: str


# ── Customization chatbot ──────────────────────────────────────────────────────

class CustomizeChatMessage(BaseModel):
    role: str    # "user" | "assistant"
    content: str


class CustomizeChange(BaseModel):
    type: str    # "character" | "evidence"
    targetId: str
    field: str
    value: Any


class CustomizeRequest(BaseModel):
    message: str
    mysterySummary: dict          # lightweight: {title, characters:[{id,name,role}], evidence:[{id,name}]}
    chatHistory: List[CustomizeChatMessage] = []


class CustomizeResponse(BaseModel):
    response: str
    changes: Optional[List[CustomizeChange]] = None
    refused: bool = False


# ── Theme icon / character avatar generation ──────────────────────────────────

class ThemeIconRequest(BaseModel):
    themeId: str
    themeName: str
    setting: str


class ThemeIconResponse(BaseModel):
    themeId: str
    imageUrl: str   # base64 data URI


class DefaultAvatarRequest(BaseModel):
    role: str
    themeName: str


class DefaultAvatarResponse(BaseModel):
    imageUrl: str   # base64 data URI


# ── User Guide ─────────────────────────────────────────────────────────────────

class UserGuideRequest(BaseModel):
    mystery: dict   # stripped mystery (no base64 imageUrl / narrationAudio)


class UserGuideResponse(BaseModel):
    invitationText: str   # theatrical prose for players — no spoilers
    gmScript: str         # markdown-formatted GM running script
