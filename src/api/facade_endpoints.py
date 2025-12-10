"""
FastAPI endpoints that expose OSCFacade methods via REST API.

This module provides a complete REST API for all facade operations:
- Natural language generation
- SML/DSL conversion
- Database operations
- Playback (note: playback endpoints return immediately, audio plays on server)
- Search and export

All Pydantic models from the facade are reused directly as request/response models.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from src.controller.osc_facade import (
    OSCFacade,
    NLToSMLRequest,
    NLToSMLResponse,
    DSLLoadConfig,
    DSLLoadResult,
    ClipSearchRequest,
    ClipDSLResponse,
    DSLProjectModel,
    PlaybackConfig,
    MidiExportOptions,
    MidiExportResult,
)


router = APIRouter(prefix="/facade", tags=["facade"])

# Singleton facade instance
_facade: Optional[OSCFacade] = None


def get_facade() -> OSCFacade:
    """Get or create the facade singleton."""
    global _facade
    if _facade is None:
        _facade = OSCFacade()
    return _facade


# -----------------------------
# Natural Language Endpoints
# -----------------------------

@router.post("/nl/clip-to-sml", response_model=NLToSMLResponse)
async def nl_clip_to_sml(request: NLToSMLRequest) -> NLToSMLResponse:
    """
    Generate SML clip from natural language using LangGraph + OpenAI.
    
    Requires OPENAI_API_KEY environment variable.
    
    Example:
        POST /facade/nl/clip-to-sml
        {"text": "Create a C major scale, quarter notes"}
    """
    facade = get_facade()
    try:
        return await facade.natural_language_clip_to_sml(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nl/clip-to-db", response_model=int)
async def nl_clip_to_db(request: NLToSMLRequest) -> int:
    """
    Complete pipeline: Natural Language → SML → DSL → Database.
    
    Returns the clip_id of the created clip.
    
    Example:
        POST /facade/nl/clip-to-db
        {"text": "Create a jazzy bass line in F"}
    """
    facade = get_facade()
    try:
        return await facade.natural_language_clip_to_db(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# SML/DSL Conversion Endpoints
# -----------------------------

@router.post("/sml/clip-to-dsl", response_model=Dict[str, Any])
async def sml_clip_to_dsl(sml_clip: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert SML clip format to DSL clip format.
    
    Example:
        POST /facade/sml/clip-to-dsl
        {
            "name": "my-clip",
            "bars": [
                {
                    "bar_index": 0,
                    "items": [
                        {"note": "C4", "duration": "quarter"}
                    ]
                }
            ]
        }
    """
    facade = get_facade()
    try:
        return facade.sml_to_dsl_clip(sml_clip)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sml/composition-to-dsl", response_model=Dict[str, Any])
async def sml_composition_to_dsl(sml_project: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert SML composition format to DSL composition format.
    
    Example:
        POST /facade/sml/composition-to-dsl
        {
            "project": {
                "name": "my-song",
                "ticks_per_quarter": 480,
                "tempo_map": [...],
                ...
            }
        }
    """
    facade = get_facade()
    try:
        return facade.sml_to_dsl_composition(sml_project)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# Database Load Endpoints
# -----------------------------

@router.post("/dsl/load", response_model=DSLLoadResult)
async def load_dsl_to_db(config: DSLLoadConfig) -> DSLLoadResult:
    """
    Load a complete DSL project into the database.
    
    Provide either 'path' (file path) or 'dsl_json' (dict).
    
    Example:
        POST /facade/dsl/load
        {"path": "src/dsl/examples/02-multi-track.json"}
        
        OR
        
        {"dsl_json": {"project": {...}}}
    """
    facade = get_facade()
    try:
        return await facade.load_dsl_to_db(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# Search Endpoints
# -----------------------------

@router.post("/clips/search", response_model=ClipDSLResponse)
async def search_clips(request: ClipSearchRequest) -> ClipDSLResponse:
    """
    Search for clips by tags or name pattern.
    
    Example:
        POST /facade/clips/search
        {"tags": ["verse", "melody"]}
        
        OR
        
        {"name_pattern": "%bass%"}
    """
    facade = get_facade()
    try:
        return await facade.search_clips(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# Export Endpoints
# -----------------------------

@router.get("/clips/{clip_id}/dsl", response_model=Dict[str, Any])
async def clip_to_dsl(clip_id: int) -> Dict[str, Any]:
    """
    Export a single clip to DSL format.
    
    Example:
        GET /facade/clips/1/dsl
    """
    facade = get_facade()
    try:
        return await facade.clip_to_dsl(clip_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/compositions/{composition_id}/dsl", response_model=DSLProjectModel)
async def composition_to_dsl(composition_id: int) -> DSLProjectModel:
    """
    Export a complete composition to DSL format.
    
    Returns the full project structure with clip library.
    
    Example:
        GET /facade/compositions/1/dsl
    """
    facade = get_facade()
    try:
        return await facade.composition_to_dsl(composition_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# -----------------------------
# MIDI Export Endpoints
# -----------------------------

@router.post("/compositions/{composition_id}/midi", response_model=MidiExportResult)
async def composition_to_midi(
    composition_id: int,
    options: MidiExportOptions
) -> MidiExportResult:
    """
    Export composition to MIDI file.
    
    Example:
        POST /facade/compositions/1/midi
        {"output_path": "output.mid"}
    """
    facade = get_facade()
    try:
        return await facade.dsl_to_midi_file(composition_id, options)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# Playback Endpoints
# -----------------------------
# Note: These endpoints trigger playback on the SERVER side.
# For client-side playback, use MIDI export endpoints instead.

class PlaySMLRequest(BaseModel):
    """Request to play an SML clip."""
    sml_clip: Dict[str, Any]
    config: PlaybackConfig


class PlayNLRequest(BaseModel):
    """Request to generate and play from natural language."""
    nl_request: NLToSMLRequest
    config: PlaybackConfig


@router.post("/playback/sml", response_model=Dict[str, str])
async def play_clip_from_sml(
    request: PlaySMLRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """
    Play an SML clip (server-side audio).
    
    Note: This plays audio on the server. The endpoint returns immediately
    and playback happens in the background.
    
    Example:
        POST /facade/playback/sml
        {
            "sml_clip": {"name": "test", "bars": [...]},
            "config": {"sf2_path": "FluidR3_GM.sf2", "bpm": 120}
        }
    """
    facade = get_facade()
    
    async def play_in_background():
        try:
            await facade.play_clip_from_sml(request.sml_clip, request.config)
        except Exception as e:
            print(f"Playback error: {e}")
    
    background_tasks.add_task(play_in_background)
    return {"status": "playing", "message": "Playback started on server"}


@router.post("/playback/nl", response_model=NLToSMLResponse)
async def play_clip_from_nl(
    request: PlayNLRequest,
    background_tasks: BackgroundTasks
) -> NLToSMLResponse:
    """
    Generate from natural language and play (server-side audio).
    
    Returns the generated SML clip. Playback happens in background.
    
    Example:
        POST /facade/playback/nl
        {
            "nl_request": {"text": "Create a C major scale"},
            "config": {"sf2_path": "FluidR3_GM.sf2", "bpm": 120}
        }
    """
    facade = get_facade()
    
    try:
        # Generate SML first (synchronously to return it)
        sml_response = await facade.natural_language_clip_to_sml(request.nl_request)
        
        # Play in background
        async def play_in_background():
            try:
                await facade.play_clip_from_sml(sml_response.sml, request.config)
            except Exception as e:
                print(f"Playback error: {e}")
        
        background_tasks.add_task(play_in_background)
        return sml_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/playback/clip/{clip_id}", response_model=Dict[str, str])
async def play_clip_from_db(
    clip_id: int,
    config: PlaybackConfig,
    background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """
    Play a clip from database (server-side audio).
    
    Example:
        POST /facade/playback/clip/1
        {"sf2_path": "FluidR3_GM.sf2", "bpm": 140, "loop": false}
    """
    facade = get_facade()
    
    async def play_in_background():
        try:
            await facade.play_clip(clip_id, config)
        except Exception as e:
            print(f"Playback error: {e}")
    
    background_tasks.add_task(play_in_background)
    return {"status": "playing", "clip_id": clip_id}
