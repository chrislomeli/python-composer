# test_osc_facade.py
# Integration and unit tests for OSCFacade

import json
import sys
from pathlib import Path

import pytest

# Add project root to path (same pattern as test_clip_service.py)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.controller.osc_facade import (  # type: ignore
    OSCFacade,
    DSLLoadConfig,
    ClipSearchRequest,
    DSLProjectModel,
    MidiExportOptions,
)
from src.repository import get_database, reset_database  # type: ignore
from src.core.schema import metadata  # type: ignore
from src.services import ClipService  # type: ignore


# -----------------------------
# Helpers
# -----------------------------

async def init_test_facade():
    """Initialize an in-memory SQLite DB and OSCFacade wired to it."""
    reset_database()
    db = get_database("sqlite:///:memory:", echo=False)
    await db.create_tables(metadata)
    facade = OSCFacade()
    return db, facade


# -----------------------------
# Pure SML/DSL conversion tests
# -----------------------------

def test_sml_to_dsl_clip_basic():
    """sml_to_dsl_clip should convert a simple SML clip into spec DSL format."""
    # Ensure facade uses SQLite-backed Database (no Postgres driver needed)
    reset_database()
    get_database("sqlite:///:memory:", echo=False)
    facade = OSCFacade()

    sml_clip = {
        "clip_id": 1,
        "name": "test-clip",
        "track_name": "lead",
        "bars": [
            {
                "bar_index": 0,
                "items": [
                    {"note": "C4", "duration": "quarter"},
                    {"note": "E4", "duration": "quarter"},
                    {"rest": "quarter"},
                ],
            }
        ],
    }

    dsl_clip = facade.sml_to_dsl_clip(sml_clip)

    assert dsl_clip["name"] == "test-clip"
    assert "bars" in dsl_clip and len(dsl_clip["bars"]) == 1

    bar0 = dsl_clip["bars"][0]
    assert "notes" in bar0 and len(bar0["notes"]) == 3

    first_note = bar0["notes"][0]
    # C4 should map to MIDI 60
    assert first_note["absolute_pitch"] == 60
    assert first_note["duration"] > 0


def test_sml_to_dsl_composition_basic():
    """sml_to_dsl_composition should produce a minimal spec-compliant composition dict."""
    reset_database()
    get_database("sqlite:///:memory:", echo=False)
    facade = OSCFacade()

    sml_project = {
        "project": {
            "name": "test-song",
            "ticks_per_quarter": 480,
            "tempo_map": [{"bar": 1, "tempo_bpm": 120}],
            "tracks": {
                "lead": {
                    "clips": [
                        {
                            "clip_instance_id": "lead_1",
                            "clip_id": 1,
                            "start_bar": 1,
                            "length_bars": 2,
                        }
                    ]
                }
            },
        }
    }

    dsl_comp = facade.sml_to_dsl_composition(sml_project)

    assert dsl_comp["name"] == "test-song"
    assert dsl_comp["ticks_per_quarter"] == 480
    assert "tracks" in dsl_comp and len(dsl_comp["tracks"]) == 1

    track = dsl_comp["tracks"][0]
    assert track["name"] == "lead"
    # Two bars should have been expanded from length_bars=2
    assert len(track["bars"]) == 2


# -----------------------------
# DB-backed facade tests (SQLite, async)
# -----------------------------

@pytest.mark.asyncio
async def test_load_dsl_to_db_and_export_composition():
    """load_dsl_to_db should create clips + composition, and composition_to_dsl should round-trip."""
    db, facade = await init_test_facade()

    example_path = (
        Path(__file__).resolve().parents[2]
        / "dsl"
        / "examples"
        / "02-multi-track.json"
    )
    assert example_path.is_file()

    config = DSLLoadConfig(path=str(example_path))
    result = await facade.load_dsl_to_db(config)

    # There are 3 clips in the example clip_library
    assert result.composition_id > 0
    assert len(result.clip_ids) == 3

    # Export the composition back to DSL project
    dsl_project = await facade.composition_to_dsl(result.composition_id)
    project = dsl_project.project

    assert project["name"] == "multi_track_example"
    assert "tracks" in project and len(project["tracks"]) == 2
    assert "clip_library" in project and len(project["clip_library"]) == 3


@pytest.mark.asyncio
async def test_clip_to_dsl_after_insertion():
    """clip_to_dsl should return a flattened DSL clip view from DB data."""
    db, facade = await init_test_facade()
    clip_service = ClipService(database=db)

    dsl_clip_input = {
        "name": "test-clip",
        "track_name": "lead",
        "bars": [
            {
                "bar_index": 0,
                "notes": [
                    {"absolute_pitch": 60, "start": 0.0, "duration": 1.0, "is_rest": False},
                    {"absolute_pitch": 64, "start": 1.0, "duration": 1.0, "is_rest": False},
                ],
                "velocity_curve": [
                    {"time": 0, "value": 90},
                    {"time": 4, "value": 100},
                ],
            }
        ],
    }

    clip_id = await clip_service.create_clip_from_dsl(dsl_clip_input)
    dsl_clip = await facade.clip_to_dsl(clip_id)

    assert dsl_clip["clip_id"] == clip_id
    assert dsl_clip["name"] == "test-clip"
    assert "notes" in dsl_clip and len(dsl_clip["notes"]) == 2

    # start_beat should reflect per-bar start (bar_index=0 → no offset)
    starts = sorted(n["start_beat"] for n in dsl_clip["notes"] if not n.get("is_rest"))
    assert starts == [0.0, 1.0]


@pytest.mark.asyncio
async def test_search_clips_by_tags_and_name():
    """search_clips should support tag-based and name-pattern search, returning DSL clips."""
    db, facade = await init_test_facade()
    clip_service = ClipService(database=db)

    # Create a few tagged clips
    base_bar = {
        "bar_index": 0,
        "notes": [
            {"absolute_pitch": 60, "start": 0.0, "duration": 1.0, "is_rest": False},
        ],
    }

    clips = [
        {"name": "melody-verse", "track_name": "melody", "tags": ["melody", "verse"], "bars": [base_bar]},
        {"name": "bass-groove", "track_name": "bass", "tags": ["bass"], "bars": [base_bar]},
        {"name": "melody-chorus", "track_name": "melody", "tags": ["melody", "chorus"], "bars": [base_bar]},
    ]

    for c in clips:
        await clip_service.create_clip_from_dsl(c)

    # Search by tag "melody"
    tag_request = ClipSearchRequest(tags=["melody"])
    tag_result = await facade.search_clips(tag_request)

    tag_names = sorted(c["name"] for c in tag_result.clips)
    assert tag_names == ["melody-chorus", "melody-verse"]

    # Search by name pattern for bass
    name_request = ClipSearchRequest(name_pattern="%bass%")
    name_result = await facade.search_clips(name_request)

    assert len(name_result.clips) == 1
    assert name_result.clips[0]["name"] == "bass-groove"


# -----------------------------
# MIDI export (no DB usage)
# -----------------------------

@pytest.mark.asyncio
async def test_dsl_to_midi_file_produces_bytes(tmp_path: Path):
    """dsl_to_midi_file should return non-empty MIDI bytes and optionally write a file."""
    # Use SQLite-backed DB to avoid any Postgres driver requirements
    reset_database()
    get_database("sqlite:///:memory:", echo=False)
    facade = OSCFacade()

    example_path = (
        Path(__file__).resolve().parents[2]
        / "dsl"
        / "examples"
        / "02-multi-track.json"
    )
    with example_path.open("r", encoding="utf-8") as f:
        dsl_json = json.load(f)

    project_model = DSLProjectModel(project=dsl_json["project"])
    out_path = tmp_path / "test_output.mid"

    options = MidiExportOptions(output_path=str(out_path), include_all_tracks=True)

    result = facade.dsl_to_midi_file(project_model, options)

    assert isinstance(result.midi_bytes, bytes)
    assert len(result.midi_bytes) > 0
    # File should also exist on disk
    assert out_path.is_file()
