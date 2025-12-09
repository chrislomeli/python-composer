# test_dsl_parser.py
# Test suite for DSL parser

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.dsl.dsl_parser import DSLParser



def test_basic_clip_parsing():
    """Test parsing a simple clip from DSL."""
    dsl = {
        "project": {
            "name": "test_project",
            "ticks_per_quarter": 480,
            "tempo_map": [{"bar": 1, "tempo_bpm": 120}],
            "meter_map": [{"bar": 1, "numerator": 4, "denominator": 4}],
            "key_map": [{"bar": 1, "key": "C", "mode": "major"}],
            "tracks": {},
            "clip_library": [
                {
                    "clip_id": 1,
                    "name": "simple-clip",
                    "notes": [
                        {"pitch": 60, "start_beat": 0.0, "duration_beats": 1.0},
                        {"pitch": 62, "start_beat": 1.0, "duration_beats": 1.0}
                    ]
                }
            ]
        }
    }
    
    parser = DSLParser()
    composition = parser.parse_project(dsl)
    
    assert composition.name == "test_project"
    assert len(parser.clip_library) == 1
    assert parser.clip_library[1].name == "simple-clip"
    assert len(parser.clip_library[1].bars) == 1  # All notes in first bar
    
    print("✓ test_basic_clip_parsing passed")


def test_multi_bar_clip():
    """Test parsing a clip that spans multiple bars."""
    dsl = {
        "project": {
            "name": "multi_bar_test",
            "ticks_per_quarter": 480,
            "tempo_map": [{"bar": 1, "tempo_bpm": 120}],
            "meter_map": [{"bar": 1, "numerator": 4, "denominator": 4}],
            "key_map": [{"bar": 1, "key": "C", "mode": "major"}],
            "tracks": {},
            "clip_library": [
                {
                    "clip_id": 2,
                    "name": "two-bar-clip",
                    "notes": [
                        # Bar 0
                        {"pitch": 60, "start_beat": 0.0, "duration_beats": 1.0},
                        {"pitch": 62, "start_beat": 1.0, "duration_beats": 1.0},
                        # Bar 1
                        {"pitch": 64, "start_beat": 4.0, "duration_beats": 1.0},
                        {"pitch": 65, "start_beat": 5.0, "duration_beats": 1.0}
                    ]
                }
            ]
        }
    }
    
    parser = DSLParser()
    composition = parser.parse_project(dsl)
    
    clip = parser.clip_library[2]
    assert len(clip.bars) == 2  # Notes span 2 bars
    assert clip.bars[0].bar_index == 0
    assert clip.bars[1].bar_index == 1
    
    print("✓ test_multi_bar_clip passed")


def test_track_with_clip_instances():
    """Test parsing tracks with clip instances."""
    dsl = {
        "project": {
            "name": "track_test",
            "ticks_per_quarter": 480,
            "tempo_map": [{"bar": 1, "tempo_bpm": 120}],
            "meter_map": [{"bar": 1, "numerator": 4, "denominator": 4}],
            "key_map": [{"bar": 1, "key": "C", "mode": "major"}],
            "tracks": {
                "melody": {
                    "instrument": {
                        "name": "piano",
                        "midi_channel": 0
                    },
                    "clips": [
                        {
                            "clip_instance_id": "melody_1",
                            "clip_id": 3,
                            "start_bar": 1,
                            "length_bars": 2
                        }
                    ]
                }
            },
            "clip_library": [
                {
                    "clip_id": 3,
                    "name": "melody-phrase",
                    "notes": [
                        {"pitch": 60, "start_beat": 0.0, "duration_beats": 1.0}
                    ]
                }
            ]
        }
    }
    
    parser = DSLParser()
    composition = parser.parse_project(dsl)
    
    assert len(composition.tracks) == 1
    track = composition.tracks[0]
    assert track.name == "melody"
    assert len(track.bars) == 2  # length_bars = 2
    assert track.bars[0].bar_index == 1  # start_bar = 1
    assert track.bars[0].clip_id == 3
    
    print("✓ test_track_with_clip_instances passed")


def test_bar_overrides():
    """Test parsing bar-level expression overrides."""
    dsl = {
        "project": {
            "name": "override_test",
            "ticks_per_quarter": 480,
            "tempo_map": [{"bar": 1, "tempo_bpm": 120}],
            "meter_map": [{"bar": 1, "numerator": 4, "denominator": 4}],
            "key_map": [{"bar": 1, "key": "C", "mode": "major"}],
            "tracks": {
                "lead": {
                    "instrument": {
                        "name": "synth",
                        "midi_channel": 0
                    },
                    "clips": [
                        {
                            "clip_instance_id": "lead_1",
                            "clip_id": 4,
                            "start_bar": 1,
                            "length_bars": 1,
                            "bar_overrides": [
                                {
                                    "bar_index": 0,
                                    "velocity_curve": [
                                        {"time": 0, "value": 70},
                                        {"time": 4, "value": 110}
                                    ],
                                    "cc_lanes": {
                                        "1": [{"time": 0, "value": 64}],
                                        "11": [{"time": 0, "value": 100}]
                                    },
                                    "pitch_bend_curve": [
                                        {"time": 0, "value": 0},
                                        {"time": 2, "value": 100}
                                    ],
                                    "metadata": {"tag": "crescendo"}
                                }
                            ]
                        }
                    ]
                }
            },
            "clip_library": [
                {
                    "clip_id": 4,
                    "name": "synth-lead",
                    "notes": [
                        {"pitch": 72, "start_beat": 0.0, "duration_beats": 2.0}
                    ]
                }
            ]
        }
    }
    
    parser = DSLParser()
    composition = parser.parse_project(dsl)
    
    clip = parser.clip_library[4]
    clip_bar = clip.bars[0]
    
    assert clip_bar.expression is not None
    assert clip_bar.expression.velocity_curve is not None
    assert len(clip_bar.expression.velocity_curve) == 2
    assert clip_bar.expression.velocity_curve[0]["value"] == 70
    assert clip_bar.expression.velocity_curve[1]["value"] == 110
    
    assert clip_bar.expression.cc is not None
    assert 1 in clip_bar.expression.cc
    assert 11 in clip_bar.expression.cc
    
    assert clip_bar.expression.pitch_bend_curve is not None
    assert clip_bar.expression.metadata == {"tag": "crescendo"}
    
    print("✓ test_bar_overrides passed")


def test_database_format_conversion():
    """Test conversion to database-ready format."""
    dsl = {
        "project": {
            "name": "db_test",
            "ticks_per_quarter": 480,
            "tempo_map": [{"bar": 1, "tempo_bpm": 140}],
            "meter_map": [{"bar": 1, "numerator": 4, "denominator": 4}],
            "key_map": [{"bar": 1, "key": "D", "mode": "minor"}],
            "tracks": {
                "bass": {
                    "instrument": {"name": "bass", "midi_channel": 1},
                    "clips": [
                        {
                            "clip_instance_id": "bass_1",
                            "clip_id": 5,
                            "start_bar": 1,
                            "length_bars": 1
                        }
                    ]
                }
            },
            "clip_library": [
                {
                    "clip_id": 5,
                    "name": "bass-line",
                    "notes": [
                        {"pitch": 36, "start_beat": 0.0, "duration_beats": 0.5}
                    ]
                }
            ]
        }
    }
    
    parser = DSLParser()
    composition = parser.parse_project(dsl)
    db_format = parser.to_database_format(composition)
    
    assert "composition" in db_format
    assert "clips" in db_format
    assert "tracks" in db_format
    
    assert db_format["composition"]["name"] == "db_test"
    assert db_format["composition"]["tempo_bpm"] == 140
    assert db_format["composition"]["ticks_per_quarter"] == 480
    
    assert len(db_format["clips"]) == 1
    assert db_format["clips"][0]["id"] == 5
    assert db_format["clips"][0]["name"] == "bass-line"
    
    assert len(db_format["tracks"]) == 1
    assert db_format["tracks"][0]["name"] == "bass"
    
    print("✓ test_database_format_conversion passed")


def test_complex_project():
    """Test parsing a complex project with multiple tracks and clips."""
    dsl = {
        "project": {
            "name": "complex_project",
            "ticks_per_quarter": 480,
            "tempo_map": [{"bar": 1, "tempo_bpm": 120}],
            "meter_map": [{"bar": 1, "numerator": 4, "denominator": 4}],
            "key_map": [{"bar": 1, "key": "C", "mode": "major"}],
            "tracks": {
                "lead": {
                    "instrument": {"name": "lead", "midi_channel": 0},
                    "clips": [
                        {
                            "clip_instance_id": "lead_1",
                            "clip_id": 10,
                            "start_bar": 1,
                            "length_bars": 2
                        },
                        {
                            "clip_instance_id": "lead_2",
                            "clip_id": 11,
                            "start_bar": 3,
                            "length_bars": 2
                        }
                    ]
                },
                "bass": {
                    "instrument": {"name": "bass", "midi_channel": 1},
                    "clips": [
                        {
                            "clip_instance_id": "bass_1",
                            "clip_id": 12,
                            "start_bar": 1,
                            "length_bars": 4
                        }
                    ]
                }
            },
            "clip_library": [
                {
                    "clip_id": 10,
                    "name": "lead-intro",
                    "notes": [{"pitch": 60, "start_beat": 0.0, "duration_beats": 1.0}]
                },
                {
                    "clip_id": 11,
                    "name": "lead-verse",
                    "notes": [{"pitch": 64, "start_beat": 0.0, "duration_beats": 1.0}]
                },
                {
                    "clip_id": 12,
                    "name": "bass-pattern",
                    "notes": [{"pitch": 36, "start_beat": 0.0, "duration_beats": 0.5}]
                }
            ]
        }
    }
    
    parser = DSLParser()
    composition = parser.parse_project(dsl)
    
    assert len(composition.tracks) == 2
    assert len(parser.clip_library) == 3
    
    # Check lead track
    lead_track = [t for t in composition.tracks if t.name == "lead"][0]
    assert len(lead_track.bars) == 4  # 2 + 2 bars
    
    # Check bass track
    bass_track = [t for t in composition.tracks if t.name == "bass"][0]
    assert len(bass_track.bars) == 4
    
    print("✓ test_complex_project passed")


def run_all_tests():
    """Run all test cases."""
    print("Running DSL Parser Tests...\n")
    
    tests = [
        test_basic_clip_parsing,
        test_multi_bar_clip,
        test_track_with_clip_instances,
        test_bar_overrides,
        test_database_format_conversion,
        test_complex_project
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
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
    success = run_all_tests()
    sys.exit(0 if success else 1)
