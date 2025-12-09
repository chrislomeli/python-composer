# FastAPI app exposing SML/DSL → DB operations

from typing import List, Dict, Any, Optional

from fastapi import FastAPI, Depends
from pydantic import BaseModel

from src.dsl.sml_ast import clip_from_smil_dict, composition_from_smil_dict
from src.services import ClipService, CompositionService


app = FastAPI(title="OSC MVP API", version="0.1.0")


# -----------------------------
# Dependency providers
# -----------------------------

async def get_clip_service() -> ClipService:
    """Provide a ClipService instance (uses shared async DB)."""
    return ClipService()


async def get_composition_service() -> CompositionService:
    """Provide a CompositionService instance (uses shared async DB)."""
    return CompositionService()


# -----------------------------
# Request models (SML / composition)
# -----------------------------

class SMLBar(BaseModel):
    """Minimal SML bar representation accepted by the API.

    This is intentionally loose to allow experimenting with different SML
    structures. The important fields are:
    - bar_index / number
    - items: list of note/rest dicts, e.g. {"note": "C4", "duration": "quarter"}.
    """

    bar_index: Optional[int] = None
    number: Optional[int] = None
    items: List[Dict[str, Any]]
    expression: Optional[Dict[str, Any]] = None


class SMLClipRequest(BaseModel):
    """SML clip payload.

    This matches what `clip_from_smil_dict` expects:
    {
      "clip_id": 8,
      "name": "lead-riff",
      "track_name": "lead",
      "bars": [ SMLBar, ... ]
    }
    """

    clip_id: Optional[int] = None
    name: Optional[str] = None
    track_name: Optional[str] = None
    bars: List[SMLBar]


class TrackBarRefRequest(BaseModel):
    bar_index: int
    clip_id: int
    clip_bar_index: int


class TrackRequest(BaseModel):
    name: str
    bars: List[TrackBarRefRequest]


class CompositionFromClipsRequest(BaseModel):
    name: str
    ticks_per_quarter: int = 480
    tempo_bpm: int = 120
    tracks: List[TrackRequest]


class SMLCompositionRequest(BaseModel):
    """Request body for creating a composition from an SML project.

    The expected structure matches the minimal SML project syntax used by
    composition_from_smil_dict, e.g.:

    {
      "project": {
        "name": "my-song",
        "ticks_per_quarter": 480,
        "tempo_map": [...],
        "meter_map": [...],
        "key_map":   [...],
        "tracks": {
          "lead": {
            "clips": [
              {"clip_instance_id": "lead_1", "clip_id": 8,
               "start_bar": 1, "length_bars": 2}
            ]
          }
        },
        "loops": [...]
      }
    }
    """

    project: Dict[str, Any]


# -----------------------------
# Endpoints
# -----------------------------

@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/clips/from-sml")
async def create_clip_from_sml(
    sml_clip: SMLClipRequest,
    service: ClipService = Depends(get_clip_service),
) -> Dict[str, Any]:
    """Create a reusable clip from SML input.

    Flow:
    - Accept SML clip JSON
    - Convert to AST via `clip_from_smil_dict`
    - Convert AST to spec/DSL clip dict (`to_spec_clip`)
    - Persist via `ClipService.create_clip_from_dsl`
    """

    # Convert SML payload to plain dict for the AST helper
    smil_dict = sml_clip.model_dump()
    clip_ast = clip_from_smil_dict(smil_dict)
    dsl_clip = clip_ast.to_spec_clip()

    clip_id = await service.create_clip_from_dsl(dsl_clip)
    stored = await service.get_clip_with_bars_and_notes(clip_id)

    return {"clip_id": clip_id, "clip": stored}


@app.get("/clips/by-name")
async def get_clips_by_name(
    name_pattern: str,
    service: ClipService = Depends(get_clip_service),
) -> List[Dict[str, Any]]:
    """Search clips by name pattern (SQL ILIKE pattern, e.g. "%lead%")."""

    return await service.find_clips_by_name(name_pattern)


@app.get("/clips/by-tag")
async def get_clips_by_tag(
    tag: str,
    service: ClipService = Depends(get_clip_service),
) -> List[Dict[str, Any]]:
    """Find clips that have bars whose metadata contains the given tag.

    Uses `ClipService.find_clips_by_tag` and returns serialized Pydantic models.
    """

    clips = await service.find_clips_by_tag(tag)
    return [c.model_dump() for c in clips]


@app.post("/compositions")
async def create_composition_from_clips(
    payload: CompositionFromClipsRequest,
    service: CompositionService = Depends(get_composition_service),
) -> Dict[str, Any]:
    """Create a composition using existing clips as building blocks.

    The payload references already-stored clips via (clip_id, clip_bar_index) pairs.
    No clips are re-stored; only compositions / tracks / track_bars are inserted.
    """

    dsl_comp = payload.model_dump()
    composition_id = await service.create_composition_from_dsl(dsl_comp)
    stored = await service.get_composition_with_tracks(composition_id)

    return {"composition_id": composition_id, "composition": stored}


@app.post("/compositions/from-sml")
async def create_composition_from_sml(
    payload: SMLCompositionRequest,
    service: CompositionService = Depends(get_composition_service),
) -> Dict[str, Any]:
    """Create a composition from an SML project description.

    Flow:
    - Accept SML project JSON
    - Convert to Composition AST via `composition_from_smil_dict`
    - Map AST to the DSL-like structure expected by CompositionService
    - Persist via `CompositionService.create_composition_from_dsl`
    """

    sml_dict = payload.model_dump()
    composition_ast = composition_from_smil_dict(sml_dict)

    dsl_comp = {
        "name": composition_ast.name,
        "ticks_per_quarter": composition_ast.ticks_per_quarter,
        "tempo_bpm": composition_ast.tempo_bpm,
        "tracks": [
            {
                "name": track.name,
                "bars": [
                    {
                        "bar_index": bar.bar_index,
                        "clip_id": bar.clip_id,
                        "clip_bar_index": bar.clip_bar_index,
                    }
                    for bar in track.bars
                ],
            }
            for track in composition_ast.tracks
        ],
    }

    composition_id = await service.create_composition_from_dsl(dsl_comp)
    stored = await service.get_composition_with_tracks(composition_id)

    return {"composition_id": composition_id, "composition": stored}


@app.get("/compositions/{composition_id}")
async def get_composition(
    composition_id: int,
    service: CompositionService = Depends(get_composition_service),
) -> Optional[Dict[str, Any]]:
    """Fetch a composition with all tracks and track bars."""

    return await service.get_composition_with_tracks(composition_id)
