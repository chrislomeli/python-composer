# test_osc_facade.py
# Integration and unit tests for OSCFacade

import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

# Add project root to path (same pattern as test_clip_service.py)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.controller.osc_facade import (  # type: ignore
    OSCFacade,
    DSLLoadConfig,
    ClipSearchRequest,
    DSLProjectModel,
    MidiExportOptions,
    NLToSMLRequest,
    PlaybackConfig,
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


# -----------------------------
# Natural Language Generation Tests
# -----------------------------

@pytest.mark.asyncio
async def test_natural_language_clip_to_sml_success():
    """natural_language_clip_to_sml should generate SML from NL prompt via LangGraph."""
    db, facade = await init_test_facade()
    
    # Mock the LangGraph generate_sml_clip function
    mock_sml_clip = {
        "name": "generated-clip",
        "bars": [
            {
                "bar_index": 0,
                "items": [
                    {"note": "C4", "duration": "quarter"},
                    {"note": "E4", "duration": "quarter"},
                ]
            }
        ]
    }
    
    with patch('src.graphs.clip_graph.generate_sml_clip', new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = {"sml_clip": mock_sml_clip, "error": None}
        
        request = NLToSMLRequest(text="Create a C major chord")
        response = await facade.natural_language_clip_to_sml(request)
        
        assert response.sml == mock_sml_clip
        assert response.sml["name"] == "generated-clip"
        assert len(response.sml["bars"]) == 1
        mock_gen.assert_called_once()


@pytest.mark.asyncio
async def test_natural_language_clip_to_sml_error():
    """natural_language_clip_to_sml should raise ValueError on generation error."""
    db, facade = await init_test_facade()
    
    with patch('src.graphs.clip_graph.generate_sml_clip', new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = {"error": "OpenAI API key not set", "sml_clip": None}
        
        request = NLToSMLRequest(text="Create a melody")
        
        with pytest.raises(ValueError, match="LangGraph clip generation failed"):
            await facade.natural_language_clip_to_sml(request)


@pytest.mark.asyncio
async def test_natural_language_clip_to_sml_no_clip():
    """natural_language_clip_to_sml should raise ValueError if no clip generated."""
    db, facade = await init_test_facade()
    
    with patch('src.graphs.clip_graph.generate_sml_clip', new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = {"error": None, "sml_clip": None}
        
        request = NLToSMLRequest(text="Create a melody")
        
        with pytest.raises(ValueError, match="No SML clip generated"):
            await facade.natural_language_clip_to_sml(request)


@pytest.mark.asyncio
async def test_natural_language_clip_to_db_full_pipeline():
    """natural_language_clip_to_db should complete NL → SML → DSL → DB pipeline."""
    db, facade = await init_test_facade()
    
    mock_sml_clip = {
        "name": "nl-generated",
        "bars": [
            {
                "bar_index": 0,
                "items": [{"note": "C4", "duration": "quarter"}]
            }
        ]
    }
    
    with patch('src.graphs.clip_graph.generate_sml_clip', new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = {"sml_clip": mock_sml_clip, "error": None}
        
        request = NLToSMLRequest(text="Create a simple melody")
        clip_id = await facade.natural_language_clip_to_db(request)
        
        # Verify clip was stored
        assert clip_id > 0
        
        # Verify we can retrieve it
        stored_clip = await facade.clip_to_dsl(clip_id)
        assert stored_clip["name"] == "nl-generated"
        assert len(stored_clip["notes"]) > 0


@pytest.mark.asyncio
async def test_natural_language_composition_to_sml_not_implemented():
    """natural_language_composition_to_sml should raise NotImplementedError."""
    db, facade = await init_test_facade()
    
    request = NLToSMLRequest(text="Create a song")
    
    with pytest.raises(NotImplementedError, match="Composition graph not yet implemented"):
        await facade.natural_language_composition_to_sml(request)


# -----------------------------
# Playback Tests (mocked)
# -----------------------------

@pytest.mark.asyncio
async def test_play_clip_from_sml():
    """play_clip_from_sml should convert SML to DSL and call play_clip."""
    db, facade = await init_test_facade()
    
    sml_clip = {
        "name": "test-playback",
        "bars": [
            {
                "bar_index": 0,
                "items": [{"note": "C4", "duration": "quarter"}]
            }
        ]
    }
    
    config = PlaybackConfig(bpm=120, loop=False)
    
    with patch('src.controller.osc_facade.play_clip') as mock_play:
        await facade.play_clip_from_sml(sml_clip, config)
        
        # Verify play_clip was called with DSL format
        mock_play.assert_called_once()
        call_args = mock_play.call_args
        assert call_args.kwargs["bpm"] == 120
        assert call_args.kwargs["loop"] is False
        assert "clip_data" in call_args.kwargs


@pytest.mark.asyncio
async def test_play_clip_from_nl():
    """play_clip_from_nl should generate SML, play it, and return the SML."""
    db, facade = await init_test_facade()
    
    mock_sml_clip = {
        "name": "nl-playback",
        "bars": [
            {
                "bar_index": 0,
                "items": [{"note": "C4", "duration": "quarter"}]
            }
        ]
    }
    
    with patch('src.graphs.clip_graph.generate_sml_clip', new_callable=AsyncMock) as mock_gen, \
         patch('src.controller.osc_facade.play_clip') as mock_play:
        
        mock_gen.return_value = {"sml_clip": mock_sml_clip, "error": None}
        
        request = NLToSMLRequest(text="Create a melody")
        config = PlaybackConfig(bpm=140, loop=True)
        
        response = await facade.play_clip_from_nl(request, config)
        
        # Should return the generated SML
        assert response.sml == mock_sml_clip
        
        # Should have called play_clip
        mock_play.assert_called_once()
        call_args = mock_play.call_args
        assert call_args.kwargs["bpm"] == 140
        assert call_args.kwargs["loop"] is True


@pytest.mark.asyncio
async def test_play_clip_from_db():
    """play_clip should retrieve clip from DB and play it."""
    db, facade = await init_test_facade()
    clip_service = ClipService(database=db)
    
    # Create a clip in DB
    dsl_clip_input = {
        "name": "stored-clip",
        "bars": [
            {
                "bar_index": 0,
                "notes": [
                    {"absolute_pitch": 60, "start": 0.0, "duration": 1.0, "is_rest": False}
                ]
            }
        ]
    }
    
    clip_id = await clip_service.create_clip_from_dsl(dsl_clip_input)
    
    config = PlaybackConfig(bpm=100, loop=False)
    
    with patch('src.controller.osc_facade.play_clip') as mock_play:
        await facade.play_clip(clip_id, config)
        
        # Verify play_clip was called
        mock_play.assert_called_once()
        call_args = mock_play.call_args
        assert call_args.kwargs["bpm"] == 100
        assert "clip_data" in call_args.kwargs


@pytest.mark.asyncio
async def test_play_composition_not_implemented():
    """play_composition should raise NotImplementedError."""
    db, facade = await init_test_facade()
    
    config = PlaybackConfig(bpm=120)
    
    with pytest.raises(NotImplementedError):
        await facade.play_composition(1, config)


# -----------------------------
# Error Handling Tests
# -----------------------------

@pytest.mark.asyncio
async def test_clip_to_dsl_not_found():
    """clip_to_dsl should raise ValueError if clip doesn't exist."""
    db, facade = await init_test_facade()
    
    with pytest.raises(ValueError, match="Clip 999 not found"):
        await facade.clip_to_dsl(999)


@pytest.mark.asyncio
async def test_composition_to_dsl_not_found():
    """composition_to_dsl should raise ValueError if composition doesn't exist."""
    db, facade = await init_test_facade()
    
    with pytest.raises(ValueError, match="Composition 999 not found"):
        await facade.composition_to_dsl(999)


@pytest.mark.asyncio
async def test_load_dsl_to_db_no_path_or_json():
    """load_dsl_to_db should raise ValueError if neither path nor dsl_json provided."""
    db, facade = await init_test_facade()
    
    config = DSLLoadConfig()  # Empty config
    
    with pytest.raises(ValueError, match="Must provide either path or dsl_json"):
        await facade.load_dsl_to_db(config)


@pytest.mark.asyncio
async def test_load_dsl_to_db_from_json():
    """load_dsl_to_db should accept dsl_json directly instead of path."""
    db, facade = await init_test_facade()
    
    example_path = (
        Path(__file__).resolve().parents[2]
        / "dsl"
        / "examples"
        / "02-multi-track.json"
    )
    
    with example_path.open("r") as f:
        dsl_json = json.load(f)
    
    config = DSLLoadConfig(dsl_json=dsl_json)
    result = await facade.load_dsl_to_db(config)
    
    assert result.composition_id > 0
    assert len(result.clip_ids) == 3
    assert result.composition_name == "multi_track_example"


# -----------------------------
# Edge Cases
# -----------------------------

def test_sml_to_dsl_clip_with_rests():
    """sml_to_dsl_clip should handle rests correctly."""
    reset_database()
    get_database("sqlite:///:memory:", echo=False)
    facade = OSCFacade()
    
    sml_clip = {
        "name": "with-rests",
        "bars": [
            {
                "bar_index": 0,
                "items": [
                    {"note": "C4", "duration": "quarter"},
                    {"rest": "quarter"},
                    {"note": "E4", "duration": "half"},
                ]
            }
        ]
    }
    
    dsl_clip = facade.sml_to_dsl_clip(sml_clip)
    
    bar0 = dsl_clip["bars"][0]
    notes = bar0["notes"]
    
    # Should have 3 items (2 notes + 1 rest)
    assert len(notes) == 3
    
    # Check rest is marked
    rest_note = notes[1]
    assert rest_note.get("is_rest") is True


def test_sml_to_dsl_clip_with_expression():
    """sml_to_dsl_clip should handle expression metadata."""
    reset_database()
    get_database("sqlite:///:memory:", echo=False)
    facade = OSCFacade()
    
    sml_clip = {
        "name": "with-expression",
        "bars": [
            {
                "bar_index": 0,
                "items": [{"note": "C4", "duration": "quarter"}],
                "expression": {
                    "dynamics": "forte",
                    "articulation": "staccato"
                }
            }
        ]
    }
    
    dsl_clip = facade.sml_to_dsl_clip(sml_clip)
    
    # Expression should be preserved in the DSL format
    assert "bars" in dsl_clip
    assert len(dsl_clip["bars"]) == 1


@pytest.mark.asyncio
async def test_search_clips_empty_results():
    """search_clips should return empty list when no matches found."""
    db, facade = await init_test_facade()
    
    request = ClipSearchRequest(tags=["nonexistent"])
    result = await facade.search_clips(request)
    
    assert result.clips == []


@pytest.mark.asyncio
async def test_search_clips_combined_tags_and_name():
    """search_clips should handle both tags and name_pattern in same request."""
    db, facade = await init_test_facade()
    clip_service = ClipService(database=db)
    
    base_bar = {
        "bar_index": 0,
        "notes": [{"absolute_pitch": 60, "start": 0.0, "duration": 1.0, "is_rest": False}]
    }
    
    clips = [
        {"name": "melody-verse", "tags": ["melody"], "bars": [base_bar]},
        {"name": "bass-verse", "tags": ["bass"], "bars": [base_bar]},
    ]
    
    for c in clips:
        await clip_service.create_clip_from_dsl(c)
    
    # Search by both tag and name pattern
    request = ClipSearchRequest(tags=["melody"], name_pattern="%verse%")
    result = await facade.search_clips(request)
    
    # Should get results from both searches (may have duplicates)
    assert len(result.clips) >= 1
    names = [c["name"] for c in result.clips]
    assert "melody-verse" in names
