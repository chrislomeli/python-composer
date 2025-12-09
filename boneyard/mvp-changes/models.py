# models.py
from __future__ import annotations
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field


class CurvePoint(BaseModel):
    """A point in a CC/pitch-bend/expression curve."""
    time: float  # in beats (or seconds depending on timeline mode)
    value: float  # 0..127 for CCs, cents or 14-bit for pitchbend depending on convention


class ExpressionModel(BaseModel):
    """
    Container for expressive per-note data.
    - cc: map CC number -> list of curve points
    - pitch_bend: list of curve points (units: cents or raw depending on exporter)
    - aftertouch: list of curve points
    """
    cc: Optional[Dict[int, List[CurvePoint]]] = None
    pitch_bend: Optional[List[CurvePoint]] = None
    aftertouch: Optional[List[CurvePoint]] = None
    # allow additional vendor-specific fields
    extra: Optional[Dict[str, Any]] = None


class DynamicsModel(BaseModel):
    velocity: int = Field(..., ge=0, le=127)


class NoteModel(BaseModel):
    """
    Primary Note model for the MVP.
    - start and duration are measured in beats (float). Could be seconds if timeline uses seconds.
    - absolute_pitch: MIDI note number 0..127
    - cents_offset: fine tuning in cents (typically -100..+100)
    - expression: optional detailed per-note CC/pitch envelopes (json-serializable)
    """
    id: Optional[int] = None
    absolute_pitch: int = Field(..., ge=0, le=127)
    cents_offset: Optional[float] = 0.0

    # Timing (beats or seconds depending on composition context)
    start: float = Field(..., ge=0.0)        # fractional beats (e.g. 1.25)
    duration: float = Field(..., ge=0.0)     # length in beats

    # Basic playback fields (MIDI-friendly)
    dynamics: DynamicsModel = Field(default_factory=lambda: DynamicsModel(velocity=90))
    articulation: Optional[str] = "normal"   # e.g. "legato", "staccato", "detache"

    # routing / context
    instrument: Optional[str] = None
    track_id: Optional[int] = None

    # Optional semantic / analysis fields (useful for AI/DSL)
    scale_degree: Optional[int] = None            # 1..7 (relative to key), or None
    interval_from_prev: Optional[int] = None      # semitones (signed), or None

    # Expression / CC curves (optional, JSON-serializable)
    expression: Optional[ExpressionModel] = None

    # Misc metadata for provenance, tags, source clip, etc.
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        # allow conversion from ORM/dict-like inputs; customize as needed
        arbitrary_types_allowed = True
        json_schema_extra = {
            "examples": [
                {
                    "absolute_pitch": 62,
                    "cents_offset": -6,
                    "start": 1.25,
                    "duration": 0.5,
                    "dynamics": {"velocity": 72},
                    "articulation": "detache",
                    "instrument": "violin",
                    "track_id": 2,
                    "scale_degree": 3,
                    "interval_from_prev": 2,
                    "expression": {
                        "cc": { "1": [{"time": 0.0, "value": 64}, {"time": 0.25, "value": 80}]},
                        "pitch_bend": [{"time": 0, "value": 0}, {"time": 0.4, "value": 200}]
                    },
                    "metadata": {"source_clip_id": 8}
                }
            ]
        }
