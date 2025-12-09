from dataclasses import dataclass
from typing import List

@dataclass
class Note:
    start_unit: int
    duration_units: int
    midi_pitch: int
    velocity: int
    is_rest: bool = False

@dataclass
class Bar:
    notes: List[Note]

@dataclass
class Clip:
    id: int
    bars: List[Bar]

@dataclass
class TrackBarRef:
    bar_index: int
    clip: Clip

@dataclass
class Track:
    id: int
    name: str
    bars: List[TrackBarRef]

@dataclass
class Composition:
    id: int
    ticks_per_quarter: int
    tempo_bpm: int
    tracks: List[Track]
