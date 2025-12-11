# test_facade_api.py
# API-level tests for FastAPI facade endpoints using TestClient

import asyncio
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Add project root to path (same pattern as other tests)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.api.facade_endpoints import router as facade_router  # type: ignore
from src.repository import get_database, reset_database  # type: ignore
from src.core.schema import metadata  # type: ignore


# -----------------------------
# Fixtures
# -----------------------------

@pytest.fixture(scope="module")
def client() -> TestClient:
    """TestClient with facade router mounted and SQLite in-memory DB.

    Uses the same bootstrap pattern as src/services/tests/test_clip_service.py,
    but wired through the FastAPI facade endpoints.
    """
    reset_database()
    db = get_database("sqlite:///:memory:", echo=False)
    # Create tables synchronously before starting the app
    asyncio.run(db.create_tables(metadata))

    app = FastAPI()
    app.include_router(facade_router)

    with TestClient(app) as c:
        yield c


def _example_dsl_path() -> Path:
    """Return path to the multi-track DSL example JSON used in tests."""
    return (
        Path(__file__).resolve().parents[2]
        / "dsl"
        / "examples"
        / "02-multi-track.json"
    )


# -----------------------------
# SML/DSL conversion endpoints
# -----------------------------

def test_sml_clip_to_dsl_endpoint(client: TestClient) -> None:
    """POST /facade/sml/clip-to-dsl should convert SML clip → DSL clip."""
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

    resp = client.post("/facade/sml/clip-to-dsl", json=sml_clip)
    assert resp.status_code == 200
    data = resp.json()

    assert data["name"] == "test-clip"
    assert "bars" in data and len(data["bars"]) == 1

    bar0 = data["bars"][0]
    assert "notes" in bar0 and len(bar0["notes"]) == 3

    first_note = bar0["notes"][0]
    # C4 should map to MIDI 60
    assert first_note["absolute_pitch"] == 60
    assert first_note["duration"] > 0


# -----------------------------
# DSL load + export endpoints
# -----------------------------

def test_dsl_load_and_export_composition_endpoint(client: TestClient) -> None:
    """/facade/dsl/load then /facade/compositions/{id}/dsl should round-trip a project."""
    example_path = _example_dsl_path()
    assert example_path.is_file()

    # Load DSL into DB via facade
    resp = client.post(
        "/facade/dsl/load",
        json={"path": str(example_path)},
    )
    assert resp.status_code == 200
    load_data = resp.json()

    assert load_data["composition_id"] > 0
    assert len(load_data["clip_ids"]) == 3  # 3 clips in clip_library

    comp_id = load_data["composition_id"]

    # Export the composition back to DSL project
    resp2 = client.get(f"/facade/compositions/{comp_id}/dsl")
    assert resp2.status_code == 200

    proj_wrapper = resp2.json()
    assert "project" in proj_wrapper

    project = proj_wrapper["project"]
    assert project["name"] == "multi_track_example"
    assert "tracks" in project and len(project["tracks"]) == 2
    assert "clip_library" in project and len(project["clip_library"]) == 3


# -----------------------------
# Search + clip export endpoints
# -----------------------------

def test_clip_search_and_dsl_export_endpoints(client: TestClient) -> None:
    """/facade/clips/search and /facade/clips/{id}/dsl should operate on loaded data."""
    example_path = _example_dsl_path()

    # Ensure DB has data (idempotent if called more than once)
    resp = client.post("/facade/dsl/load", json={"path": str(example_path)})
    assert resp.status_code == 200

    # Search for bass-pattern by name pattern
    resp_search = client.post(
        "/facade/clips/search",
        json={"name_pattern": "%bass%"},
    )
    assert resp_search.status_code == 200
    search_data = resp_search.json()

    clips = search_data["clips"]
    # Expect exactly one bass clip
    assert len(clips) == 1
    clip = clips[0]
    assert "name" in clip and "bass" in clip["name"]

    clip_id = clip["clip_id"]

    # Export that clip via /facade/clips/{id}/dsl
    resp_clip = client.get(f"/facade/clips/{clip_id}/dsl")
    assert resp_clip.status_code == 200
    clip_dsl = resp_clip.json()

    assert clip_dsl["clip_id"] == clip_id
    assert clip_dsl["name"] == clip["name"]
    assert "notes" in clip_dsl and len(clip_dsl["notes"]) > 0
