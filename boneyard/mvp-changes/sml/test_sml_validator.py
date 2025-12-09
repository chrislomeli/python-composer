# test_smil_validator.py
import pytest
from smil_validator import validate_smil_bar, validate_smil_clip, SMILValidationError

# --- Valid bar sample (4 quarter notes) ---
VALID_BAR = {
    "number": 1,
    "items": [
        {"note": "C4", "duration": "quarter"},
        {"note": "E4", "duration": "quarter"},
        {"note": "G3", "duration": "quarter"},
        {"rest": "quarter"}
    ]
}

# --- Valid clip (2 bars) ---
VALID_CLIP = {
    "name": "lead-riff-intro",
    "instrument": "lead-kazoo",
    "style": "latin",
    "tempo": 120,
    "bars": [
        VALID_BAR,
        {
            "number": 2,
            "items": [
                {"note": "D4", "duration": "quarter"},
                {"note": "F4", "duration": "quarter"},
                {"note": "A4", "duration": "quarter"},
                {"rest": "quarter"}
            ]
        }
    ]
}

# --- Overflow bar (sum durations > 32 units) ---
OVERFLOW_BAR = {
    "number": 1,
    "items": [
        # use thirty-second unit = 1 unit; create 33 items to overflow 32 units
        *[{"note": "C4", "duration": "thirty_second"} for _ in range(33)]
    ]
}

# --- Invalid pitch ---
INVALID_PITCH_BAR = {
    "number": 1,
    "items": [
        {"note": "H9", "duration": "quarter"}  # H is not a valid note
    ]
}

# --- Missing duration ---
MISSING_DURATION_BAR = {
    "number": 1,
    "items": [
        {"note": "C4"}  # no duration specified
    ]
}


def test_validate_valid_bar():
    bar, err = validate_smil_bar(VALID_BAR)
    assert err is None
    assert bar is not None
    # After layout, ensure start_units/durations computed and sum == 32
    total = sum(item.duration.units for item in bar.items)  # type: ignore
    assert total == bar.units_per_bar


def test_validate_valid_clip():
    clip, err = validate_smil_clip(VALID_CLIP)
    assert err is None
    assert clip is not None
    # clip should have two bars and each bar should sum to units_per_bar
    assert len(clip.bars) == 2
    for b in clip.bars:
        total = sum(item.duration.units for item in b.items)  # type: ignore
        assert total == b.units_per_bar


def test_bar_overflow_detected():
    bar, err = validate_smil_bar(OVERFLOW_BAR)
    assert bar is None
    assert isinstance(err, SMILValidationError)
    assert "Bar validation failed" in str(err)


def test_invalid_pitch_detected():
    bar, err = validate_smil_bar(INVALID_PITCH_BAR)
    assert bar is None
    assert isinstance(err, SMILValidationError)
    assert "Invalid pitch" in str(err.details) or "Invalid pitch string" in str(err.details) or "Invalid" in str(err.details)


def test_missing_duration_detected():
    bar, err = validate_smil_bar(MISSING_DURATION_BAR)
    assert bar is None
    assert isinstance(err, SMILValidationError)
    assert "Unknown bar item" in str(err.details) or "duration" in str(err.details) or "Unknown duration token" in str(err.details)
