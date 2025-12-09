# boneyard/repo/models.py
from pydantic import BaseModel
from typing import Optional, Dict, List

class DatabaseLogin(BaseModel):
    database: str
    user: str
    password: str
    host: str
    port: int

    def toURL(self):
        return f'postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}'


class ClipModel(BaseModel):
    name: str = "untitled"
    style: str = "none"
    instrument: str = ""
    tempo_bpm: int = 120
    grid_units: int = 32
    metadata: Optional[Dict] = None

class VoiceBarModel(BaseModel):
    id: Optional[int] = None
    clip_id: int
    bar_number: int
    time_signature_numerator: int = 4
    time_signature_denominator: int = 4
    metadata: Optional[Dict] = None

class NoteModel(BaseModel):
    id: Optional[int] = None
    bar_id: int
    start_unit: int
    duration_units: int
    pitch_name: Optional[str]
    octave: Optional[int]
    velocity: int = 90
    articulation: str = "normal"
    is_rest: bool = False
    expression: Optional[float]
    microtiming_offset: Optional[int]
    metadata: Optional[Dict]

class CompositionModel(BaseModel):
    id: Optional[int] = None
    name: str
    ticks_per_quarter: int = 480
    tempo_bpm: int = 120
    time_signature_numerator: int = 4
    time_signature_denominator: int = 4
    metadata: Optional[Dict] = None

class TrackModel(BaseModel):
    id: Optional[int] = None
    composition_id: int
    name: str
    instrument: Optional[str] = None
    midi_channel: Optional[int] = 0
    group_id: Optional[int] = None
    position: int = 0
    metadata: Optional[Dict] = None

class TrackBarModel(BaseModel):
    id: Optional[int] = None
    track_id: int
    bar_index: int
    voice_bar_id: Optional[int] = None
    clip_id: Optional[int]  = None
    clip_bar_index: Optional[int] = None
    is_empty: bool = False
    metadata: Optional[Dict] = None

class TrackGroupModel(BaseModel):
    id: Optional[int]
    composition_id: int
    name: str
    metadata: Optional[Dict]

class ClipBarModel(BaseModel):
    id: Optional[int] = None
    clip_id: int                     # The clip this bar belongs to
    bar_index: int                    # Index within the clip
    velocity_curve: Optional[List[Dict]] = None          # Example: [60, 80, 100, 90]
    cc: Optional[Dict[int, List[Dict]]] = None         # CC number → list of events {type, value, time}
    pitch_bend_curve: Optional[List[Dict]] = None      # [{time, value}, ...]
    aftertouch_curve: Optional[List[Dict]] = None      # [{time, value}, ...]
    pedal_events: Optional[List[Dict]] = None          # [{time, value}, ...]
    metadata: Optional[Dict] = None