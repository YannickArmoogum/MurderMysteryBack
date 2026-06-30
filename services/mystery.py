"""Mystery assembly and streaming generation service."""
import asyncio
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import AsyncGenerator

from sqlalchemy.orm import Session

from core.schemas.schemas import (
    GenerateRequest,
    GeneratedMystery,
    GeneratedCharacter,
    EvidenceCard,
    MysteryAct,
    GMGuide,
    RevealScript,
    TimelineEvent,
    Victim,
)
from core.config import config
from prompts import PromptBuilder, character_image_prompt, narration_prompt
from services import llm as llm_svc
from services import image as image_svc
from services import tts as tts_svc


def assemble_mystery(raw: dict, req: GenerateRequest, theme_name: str, setting: str) -> GeneratedMystery:
    """Convert raw LLM dict into a validated GeneratedMystery with fallbacks."""
    def safe_str(val, fallback="") -> str:
        return str(val) if val else fallback

    def safe_list(val, fallback=None) -> list:
        return list(val) if isinstance(val, list) else (fallback or [])

    victim_raw = raw.get("victim", {})
    victim = Victim(
        name=safe_str(victim_raw.get("name"), "The Victim"),
        role=safe_str(victim_raw.get("role"), "Unknown"),
        description=safe_str(victim_raw.get("description"), ""),
    )

    chars: list[GeneratedCharacter] = []
    has_killer = False
    for i, c in enumerate(safe_list(raw.get("characters"))):
        is_killer = bool(c.get("isKiller", False))
        if is_killer:
            has_killer = True
        chars.append(GeneratedCharacter(
            id=safe_str(c.get("id"), f"char-{i+1}"),
            name=safe_str(c.get("name"), f"Character {i+1}"),
            role=safe_str(c.get("role"), "Guest"),
            publicIdentity=safe_str(c.get("publicIdentity"), ""),
            secretBackground=safe_str(c.get("secretBackground"), ""),
            personalityArchetype=safe_str(c.get("personalityArchetype"), ""),
            hiddenMotive=safe_str(c.get("hiddenMotive"), ""),
            personalObjective=safe_str(c.get("personalObjective"), ""),
            incriminatingClues=safe_list(c.get("incriminatingClues")),
            exculpatoryClues=safe_list(c.get("exculpatoryClues")),
            alibi=safe_str(c.get("alibi"), ""),
            secretOnlyTheyKnow=safe_str(c.get("secretOnlyTheyKnow"), ""),
            behaviouralGuideline=safe_str(c.get("behaviouralGuideline"), ""),
            samplePhrases=safe_list(c.get("samplePhrases")),
            symbolicDetail=safe_str(c.get("symbolicDetail"), ""),
            costume=safe_str(c.get("costume"), "Formal attire"),
            isKiller=is_killer,
            relationships=safe_list(c.get("relationships")),
        ))
    if chars and not has_killer:
        chars[0].isKiller = True

    evidence: list[EvidenceCard] = []
    for i, e in enumerate(safe_list(raw.get("evidence"))):
        ev_type = e.get("type", "physical")
        if ev_type not in ("physical", "testimony", "document", "behavioral"):
            ev_type = "physical"
        act_num = e.get("revealedInAct", 1)
        if act_num not in (1, 2, 3):
            act_num = 1
        evidence.append(EvidenceCard(
            id=safe_str(e.get("id"), f"ev-{i+1}"),
            name=safe_str(e.get("name"), f"Evidence {i+1}"),
            type=ev_type,
            description=safe_str(e.get("description"), ""),
            actsAs=safe_str(e.get("actsAs"), ""),
            revealedInAct=act_num,
        ))

    timeline: list[TimelineEvent] = []
    for t in safe_list(raw.get("timeline")):
        if not isinstance(t, dict):
            continue
        time_str = safe_str(t.get("time"))
        event_str = safe_str(t.get("event") or t.get("description"))
        if time_str or event_str:
            timeline.append(TimelineEvent(time=time_str, event=event_str))

    acts: list[MysteryAct] = []
    for act_raw in safe_list(raw.get("acts")):
        num = act_raw.get("number", len(acts) + 1)
        if num not in (1, 2, 3):
            num = len(acts) + 1
        acts.append(MysteryAct(
            number=num,
            title=safe_str(act_raw.get("title"), f"Act {num}"),
            duration=safe_str(act_raw.get("duration"), "30 minutes"),
            summary=safe_str(act_raw.get("summary"), ""),
            keyEvents=safe_list(act_raw.get("keyEvents")),
            cluesReleased=safe_list(act_raw.get("cluesReleased")),
            gmNotes=safe_str(act_raw.get("gmNotes"), ""),
        ))
    for i in range(len(acts), 3):
        acts.append(MysteryAct(
            number=i + 1, title=f"Act {i+1}", duration="30 minutes",
            summary="", keyEvents=[], cluesReleased=[], gmNotes="",
        ))

    gm_raw = raw.get("gmGuide", {})
    gm = GMGuide(
        setupInstructions=safe_list(gm_raw.get("setupInstructions")),
        roomSetup=safe_list(gm_raw.get("roomSetup")),
        lightingAndMusic=safe_str(gm_raw.get("lightingAndMusic"), ""),
        costumeNotes=safe_str(gm_raw.get("costumeNotes"), ""),
        timingBreakdown=safe_list(gm_raw.get("timingBreakdown")),
        managingDominantPlayers=safe_str(gm_raw.get("managingDominantPlayers"), ""),
        helpingStuckGroups=safe_str(gm_raw.get("helpingStuckGroups"), ""),
        printableChecklist=safe_list(gm_raw.get("printableChecklist")),
    )

    rev_raw = raw.get("revealScript", {})
    reveal = RevealScript(
        openingStatement=safe_str(rev_raw.get("openingStatement"), ""),
        timelineReconstruction=safe_str(rev_raw.get("timelineReconstruction"), ""),
        methodExplanation=safe_str(rev_raw.get("methodExplanation"), ""),
        motiveReveal=safe_str(rev_raw.get("motiveReveal"), ""),
        emotionalConclusion=safe_str(rev_raw.get("emotionalConclusion"), ""),
        optionalTwist=rev_raw.get("optionalTwist"),
    )

    return GeneratedMystery(
        id=str(uuid.uuid4()),
        title=safe_str(raw.get("title"), "A Night of Shadows"),
        theme=req.theme,
        themeName=theme_name,
        setting=setting,
        difficulty=req.difficulty,
        tone=req.tone,
        playerCount=req.playerCount,
        tagline=safe_str(raw.get("tagline"), ""),
        victim=victim,
        murderMethod=safe_str(raw.get("murderMethod"), "Unknown"),
        storyOverview=safe_str(raw.get("storyOverview"), ""),
        timeline=timeline,
        acts=acts,
        characters=chars,
        evidence=evidence,
        gmGuide=gm,
        revealScript=reveal,
        generatedAt=datetime.now(timezone.utc).isoformat(),
    )


async def _expand_character(
    skeleton: dict, char: dict, executor: ThreadPoolExecutor, language: str = "en"
) -> dict:
    """Run one dossier call and merge its rich fields onto the character skeleton."""
    merged = {k: v for k, v in char.items() if k != "brief"}
    try:
        dossier = await asyncio.get_event_loop().run_in_executor(
            executor, llm_svc.generate_character_dossier, skeleton, char, language
        )
        if isinstance(dossier, dict):
            merged.update(dossier)
    except Exception as exc:
        print(f"Dossier generation failed for {char.get('name')}: {exc}")
    return merged


def _dossier_executor(char_count: int) -> ThreadPoolExecutor:
    """Thread pool for the dossier fan-out, capped at LLM_MAX_CONCURRENCY.

    Capping the workers bounds how many dossier calls hit Anthropic at once: it
    avoids rate-limit (429) retry storms on large casts, and any wave after the
    first reuses the prompt cache the earlier wave warmed.
    """
    workers = max(1, min(char_count, config.LLM_MAX_CONCURRENCY))
    return ThreadPoolExecutor(max_workers=workers)


async def _resolve_production(production_future, core: dict, language: str) -> dict:
    """Await the concurrent production pass; if it failed under load, retry once.

    Production (acts/evidence/GM guide/reveal) runs concurrently with the dossier
    fan-out. If that wave briefly rate-limits the API, the single production call can
    fail — and silently dropping it leaves the GM Guide and Evidence empty. By the
    time we get here the dossiers are done, so a one-shot retry runs with the load
    cleared and reliably fills those sections back in.
    """
    loop = asyncio.get_event_loop()
    try:
        production = await production_future
    except Exception as exc:
        print(f"Production generation failed, retrying: {exc}")
        try:
            production = await loop.run_in_executor(
                None, llm_svc.generate_production, core, language
            )
        except Exception as exc2:
            print(f"Production retry failed: {exc2}")
            production = {}
    return production or {}


async def generate_mystery_raw(req: GenerateRequest, session: Session) -> dict:
    """Chained generation: fast core blueprint, then fan-out dossiers while the
    act/evidence/GM/reveal material is written in parallel.

    Critical path is core + slowest dossier wave; the heavier "production" content
    (acts, evidence, GM guide, reveal) overlaps the dossier fan-out instead of
    sitting in front of it, so wall-clock barely grows with cast size.
    """
    loop = asyncio.get_event_loop()
    builder = PromptBuilder(session)
    user_msg = builder.mystery_user_message(
        req.theme, req.playerCount, req.difficulty, req.tone, req.language
    )

    # Stage 1a — small, fast, gates the dossiers.
    core = await loop.run_in_executor(None, llm_svc.generate_core_blueprint, user_msg)

    core_chars = core.get("characters") or []

    # Stage 1b — runs concurrently with the dossier fan-out.
    production_future = asyncio.ensure_future(
        loop.run_in_executor(None, llm_svc.generate_production, core, req.language)
    )

    executor = _dossier_executor(len(core_chars))
    try:
        expanded = await asyncio.gather(
            *(_expand_character(core, c, executor, req.language) for c in core_chars)
        )
    finally:
        executor.shutdown(wait=False)

    production = await _resolve_production(production_future, core, req.language)

    raw = {**core, **production, "characters": list(expanded)}
    return raw


async def mystery_stream_generator(req: GenerateRequest, session: Session) -> AsyncGenerator[str, None]:
    """SSE event generator for full mystery creation with images and audio."""
    def sse(data: dict) -> str:
        return f"data: {json.dumps(data)}\n\n"

    try:
        builder = PromptBuilder(session)
        theme_name, setting = builder.theme_info(req.theme, req.language)

        yield sse({"step": "prompt", "message": "Crafting the mystery premise...", "progress": 5})
        await asyncio.sleep(0)

        user_msg = builder.mystery_user_message(
            req.theme, req.playerCount, req.difficulty, req.tone, req.language
        )

        yield sse({"step": "llm", "message": "Designing the mystery blueprint with Claude...", "progress": 10})
        await asyncio.sleep(0)

        loop = asyncio.get_event_loop()

        # Stage 1a — fast core blueprint (facts, timeline, character skeletons).
        core = await loop.run_in_executor(None, llm_svc.generate_core_blueprint, user_msg)

        core_chars = core.get("characters") or []
        total_chars = len(core_chars) or 1
        yield sse({
            "step": "blueprint_done",
            "message": f"Blueprint ready. Writing {len(core_chars)} character dossiers in parallel...",
            "progress": 25,
        })
        await asyncio.sleep(0)

        # Stage 1b — acts/evidence/GM/reveal, generated concurrently with the dossiers.
        production_future = asyncio.ensure_future(
            loop.run_in_executor(None, llm_svc.generate_production, core, req.language)
        )

        # Stage 2 — fan out one dossier call per character; stream progress as each lands.
        executor = _dossier_executor(len(core_chars))
        try:
            dossier_tasks = [
                asyncio.ensure_future(_expand_character(core, c, executor, req.language))
                for c in core_chars
            ]
            expanded: list[dict] = []
            for i, fut in enumerate(asyncio.as_completed(dossier_tasks)):
                expanded.append(await fut)
                pct = 25 + int(20 * (i + 1) / total_chars)
                yield sse({
                    "step": "dossier_progress",
                    "message": f"Character dossier {i + 1}/{len(core_chars)} written",
                    "progress": pct,
                })
                await asyncio.sleep(0)
        finally:
            executor.shutdown(wait=False)

        production = await _resolve_production(production_future, core, req.language)

        raw = {**core, **production, "characters": expanded}
        yield sse({"step": "llm_done", "message": "Story & characters complete. Building output...", "progress": 45})
        await asyncio.sleep(0)

        mystery = assemble_mystery(raw, req, theme_name, setting)

        yield sse({"step": "images", "message": "Generating character portraits (free)...", "progress": 50})
        await asyncio.sleep(0)

        image_tasks = [
            asyncio.get_event_loop().run_in_executor(
                None,
                image_svc.generate_character_portrait,
                character_image_prompt(c.name, c.role, c.costume, theme_name),
            )
            for c in mystery.characters
        ]
        total = len(image_tasks)
        for i, coro in enumerate(asyncio.as_completed(image_tasks)):
            try:
                img_data = await coro
                mystery.characters[i].imageUrl = img_data
            except Exception:
                pass
            pct = 50 + int(30 * (i + 1) / total)
            yield sse({"step": "image_progress", "message": f"Portrait {i + 1}/{total} ready", "progress": pct})
            await asyncio.sleep(0)

        yield sse({"step": "narration", "message": "Recording opening narration with Bark...", "progress": 82})
        await asyncio.sleep(0)

        narration_text = narration_prompt(
            f"{mystery.title}. {mystery.tagline}. "
            f"The scene: {setting}. {mystery.storyOverview[:200]}"
        )
        mystery_dict = mystery.model_dump()
        try:
            audio_data = await asyncio.get_event_loop().run_in_executor(
                None, tts_svc.generate_narration, narration_text
            )
            mystery_dict["narrationAudio"] = audio_data
        except Exception:
            mystery_dict["narrationAudio"] = None

        yield sse({"step": "done", "message": "Your mystery is ready!", "progress": 100})
        await asyncio.sleep(0)
        yield sse({"step": "result", "data": mystery_dict, "progress": 100})

    except Exception as exc:
        yield sse({"step": "error", "message": str(exc), "progress": -1})
