# test_clip_service.py
# Integration tests for ClipService
import json
import sys
from pathlib import Path
import asyncio

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.services import ClipService
from src.repository import get_database, reset_database
from src.core.schema import metadata

async def setup_test_db():
    """Setup a test database in memory."""
    reset_database()
    db = get_database("sqlite:///:memory:", echo=False)
    await db.create_tables(metadata)
    return db

@pytest.mark.asyncio
async def test_create_clip_from_dsl():
    """Test creating a clip from DSL format."""
    db = await setup_test_db()
    service = ClipService(database=db)
    
    # DSL clip data
    dsl_clip = {
        "name": "test-clip",
        "track_name": "lead",
        "bars": [
            {
                "bar_index": 0,
                "notes": [
                    {
                        "absolute_pitch": 60,
                        "start": 0.0,
                        "duration": 1.0,
                        "is_rest": False
                    },
                    {
                        "absolute_pitch": 64,
                        "start": 1.0,
                        "duration": 1.0,
                        "is_rest": False
                    }
                ],
                "velocity_curve": [
                    {"time": 0, "value": 90},
                    {"time": 4, "value": 100}
                ]
            }
        ]
    }
    
    # Create clip
    clip_id = await service.create_clip_from_dsl(dsl_clip)
    assert clip_id is not None
    assert clip_id > 0
    
    # Retrieve clip
    clip = await service.get_clip_with_bars_and_notes(clip_id)
    clip_str = json.dumps(clip, indent=2)
    assert clip is not None
    assert clip["name"] == "test-clip"
    assert clip["track_name"] == "lead"
    assert len(clip["bars"]) == 1
    assert len(clip["bars"][0]["notes"]) == 2
    assert clip["bars"][0]["velocity_curve"] is not None
    
    print("✓ test_create_clip_from_dsl passed")

@pytest.mark.asyncio
async def test_create_multi_bar_clip():
    """Test creating a clip with multiple bars."""
    db = await setup_test_db()
    service = ClipService(database=db)
    
    dsl_clip = {
        "name": "multi-bar-clip",
        "bars": [
            {
                "bar_index": 0,
                "notes": [
                    {"absolute_pitch": 60, "start": 0.0, "duration": 1.0, "is_rest": False}
                ]
            },
            {
                "bar_index": 1,
                "notes": [
                    {"absolute_pitch": 64, "start": 0.0, "duration": 1.0, "is_rest": False}
                ],
                "cc": {
                    "1": [{"time": 0, "value": 64}]
                }
            }
        ]
    }
    
    clip_id = await service.create_clip_from_dsl(dsl_clip)
    clip = await service.get_clip_with_bars_and_notes(clip_id)
    
    assert len(clip["bars"]) == 2
    assert clip["bars"][0]["bar_index"] == 0
    assert clip["bars"][1]["bar_index"] == 1
    assert clip["bars"][1]["cc"] is not None
    
    print("✓ test_create_multi_bar_clip passed")

@pytest.mark.asyncio
async def test_find_clips_by_name():
    """Test searching clips by name."""
    db = await setup_test_db()
    service = ClipService(database=db)
    
    # Create test clips
    for i in range(3):
        dsl_clip = {
            "name": f"lead-clip-{i}",
            "bars": [
                {
                    "bar_index": 0,
                    "notes": [
                        {"absolute_pitch": 60, "start": 0.0, "duration": 1.0, "is_rest": False}
                    ]
                }
            ]
        }
        await service.create_clip_from_dsl(dsl_clip)
    
    # Search for clips
    results = await service.find_clips_by_name("%lead%")
    assert len(results) == 3
    
    results = await service.find_clips_by_name("%clip-1%")
    assert len(results) == 1
    assert results[0]["name"] == "lead-clip-1"
    
    print("✓ test_find_clips_by_name passed")

@pytest.mark.asyncio
async def test_delete_clip():
    """Test deleting a clip."""
    db = await setup_test_db()
    service = ClipService(database=db)
    
    dsl_clip = {
        "name": "temp-clip",
        "bars": [
            {
                "bar_index": 0,
                "notes": [
                    {"absolute_pitch": 60, "start": 0.0, "duration": 1.0, "is_rest": False}
                ]
            }
        ]
    }
    
    clip_id = await service.create_clip_from_dsl(dsl_clip)
    assert await service.get_clip_with_bars_and_notes(clip_id) is not None
    
    # Delete clip
    deleted = await service.delete_clip(clip_id)
    assert deleted is True
    
    # Verify it's gone
    assert await service.get_clip_with_bars_and_notes(clip_id) is None
    
    print("✓ test_delete_clip passed")

@pytest.mark.asyncio
async def run_all_tests():
    """Run all test cases."""
    print("Running ClipService Tests...\n")
    
    tests = [
        test_create_clip_from_dsl,
        test_create_multi_bar_clip,
        test_find_clips_by_name,
        test_delete_clip
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Tests passed: {passed}/{passed + failed}")
    print(f"Tests failed: {failed}/{passed + failed}")
    print(f"{'='*50}")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
