# models.py
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------
# 2.1 Note (Spec §2.1)
# ---------------------------------------------------------

class Note(BaseModel):
    """
    Represents a single note or rest with MIDI and semantic information.
    Matches spec §2.1 exactly.
    """
    absolute_pitch: int = Field(..., ge=0, le=127, description="MIDI pitch number (0-127)")
    start: float = Field(..., description="Start time in beats")
    duration: float = Field(..., description="Duration in beats")
    is_rest: bool = False
    
    # Contextual musical semantics
    scale_degree: Optional[int] = None
    interval_from_prev: Optional[int] = None
    cents_offset: Optional[float] = 0.0
    
    # Articulation and dynamics
    articulation: Optional[str] = None  # e.g., "detache", "staccato", "legato"
    dynamics: Optional[Dict] = None     # e.g., {"velocity": 72}
    
    # Expression (CC, pitch bend, aftertouch, pedal events)
    expression: Optional[Dict] = None

    @field_validator("absolute_pitch")
    def validate_pitch_for_rest(cls, v, info):
        if info.data.get("is_rest") and v is not None:
            raise ValueError("Rest notes should not have a pitch value")
        return v


# ---------------------------------------------------------
# 2.2 ClipBar (Spec §2.2)
# ---------------------------------------------------------

class ClipBar(BaseModel):
    """
    Represents a single bar of a clip, including MIDI expression curves.
    This is the key entity for bar-level dynamics (swells, crescendos, etc.).
    Matches spec §2.2 exactly.
    """
    id: Optional[int] = None
    clip_id: int
    bar_index: int
    
    # Bar-level expression curves
    velocity_curve: Optional[List[Dict]] = None      # [{"time":0, "value":90}, ...]
    cc: Optional[Dict[int, List[Dict]]] = None       # CC number → events [{"time":0,"value":64}, ...]
    pitch_bend_curve: Optional[List[Dict]] = None    # [{"time":0,"value":0}, {"time":4,"value":200}]
    aftertouch_curve: Optional[List[Dict]] = None
    pedal_events: Optional[List[Dict]] = None
    metadata: Optional[Dict] = None


# ---------------------------------------------------------
# 2.3 Clip (Spec §2.3)
# ---------------------------------------------------------

class Clip(BaseModel):
    """
    A reusable musical clip containing multiple bars.
    Matches spec §2.3 exactly.
    """
    id: Optional[int] = None
    name: str
    track_name: Optional[str] = None
    tags: Optional[List[str]] = None
    bars: List[ClipBar] = Field(default_factory=list)


# ---------------------------------------------------------
# 2.4 Track (Spec §2.4)
# ---------------------------------------------------------

class TrackBarRef(BaseModel):
    """
    References a specific bar from a clip for use in a track.
    Allows clip reuse with different bar selections.
    """
    bar_index: int
    clip: Clip


class Track(BaseModel):
    """
    A track in a composition, containing references to clip bars.
    Matches spec §2.4 exactly.
    """
    id: int
    name: str
    bars: List[TrackBarRef] = Field(default_factory=list)


# ---------------------------------------------------------
# 2.5 Composition (Spec §2.5)
# ---------------------------------------------------------

class Composition(BaseModel):
    """
    A complete composition with multiple tracks.
    Matches spec §2.5 exactly.
    """
    id: int
    name: str
    ticks_per_quarter: int = 480
    tempo_bpm: int = 120
    tracks: List[Track] = Field(default_factory=list)
