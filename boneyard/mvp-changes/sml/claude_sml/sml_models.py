from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from sqlalchemy import (
    Table, Column, Integer, String, Float, Boolean,
    JSON, ForeignKey, MetaData, DateTime, Text, Index
)

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class TempoMapEntry(BaseModel):
    bar: int
    tempo_bpm: float

class MeterMapEntry(BaseModel):
    bar: int
    numerator: int
    denominator: int

class KeyMapEntry(BaseModel):
    bar: int
    key: str
    mode: str

class CurvePoint(BaseModel):
    time: float
    value: float

class BarOverride(BaseModel):
    bar_index: int
    velocity_curve: Optional[List[CurvePoint]] = None
    cc_lanes: Optional[Dict[str, List[CurvePoint]]] = None
    pitch_bend_curve: Optional[List[CurvePoint]] = None
    aftertouch_curve: Optional[List[CurvePoint]] = None
    pedal_events: Optional[List[Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class ClipInstance(BaseModel):
    clip_instance_id: str
    clip_id: int  # References the global clip's clip_id
    start_bar: int
    length_bars: int
    bar_overrides: Optional[List[BarOverride]] = None

class Instrument(BaseModel):
    name: str
    midi_channel: int

class Track(BaseModel):
    instrument: Instrument
    clips: List[ClipInstance]

class Loop(BaseModel):
    start_bar: int
    length_bars: int
    repeat_count: int

class Note(BaseModel):
    pitch: Optional[int] = None
    start_beat: float
    duration_beats: float
    is_rest: Optional[bool] = False

class Clip(BaseModel):
    clip_id: int
    name: str
    style: Optional[str] = None
    tags: Optional[List[str]] = None  # Added for searching
    notes: List[Note]

class Project(BaseModel):
    name: str
    ticks_per_quarter: int
    tempo_map: List[TempoMapEntry]
    meter_map: List[MeterMapEntry]
    key_map: List[KeyMapEntry]
    tracks: Dict[str, Track]
    loops: Optional[List[Loop]] = None

class ProjectContainer(BaseModel):
    project: Project


# ============================================================================
# SQLALCHEMY TABLE DEFINITIONS
# ============================================================================

metadata = MetaData()

# Clips are now independent and shared across projects
clips = Table(
    'clips',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('clip_id', Integer, nullable=False, unique=True),  # User-facing ID
    Column('name', String(255), nullable=False),
    Column('style', String(100), nullable=True),
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Index('idx_clips_clip_id', 'clip_id'),
    Index('idx_clips_style', 'style')
)

# Tags for clips (many-to-many relationship)
clip_tags = Table(
    'clip_tags',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('clip_id', Integer, ForeignKey('clips.id', ondelete='CASCADE'), nullable=False),
    Column('tag', String(100), nullable=False),
    Index('idx_clip_tags_tag', 'tag'),
    Index('idx_clip_tags_clip_id', 'clip_id')
)

notes = Table(
    'notes',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('clip_id', Integer, ForeignKey('clips.id', ondelete='CASCADE'), nullable=False),
    Column('pitch', Integer, nullable=True),
    Column('start_beat', Float, nullable=False),
    Column('duration_beats', Float, nullable=False),
    Column('is_rest', Boolean, default=False),
    Index('idx_notes_clip_id', 'clip_id')
)

projects = Table(
    'projects',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', String(255), nullable=False, unique=True),
    Column('ticks_per_quarter', Integer, nullable=False),
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
)

tempo_map = Table(
    'tempo_map',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('project_id', Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
    Column('bar', Integer, nullable=False),
    Column('tempo_bpm', Float, nullable=False)
)

meter_map = Table(
    'meter_map',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('project_id', Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
    Column('bar', Integer, nullable=False),
    Column('numerator', Integer, nullable=False),
    Column('denominator', Integer, nullable=False)
)

key_map = Table(
    'key_map',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('project_id', Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
    Column('bar', Integer, nullable=False),
    Column('key', String(10), nullable=False),
    Column('mode', String(20), nullable=False)
)

tracks = Table(
    'tracks',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('project_id', Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
    Column('track_name', String(255), nullable=False),
    Column('instrument_name', String(255), nullable=False),
    Column('midi_channel', Integer, nullable=False)
)

# References clips by clip_id (the user-facing ID)
clip_instances = Table(
    'clip_instances',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('track_id', Integer, ForeignKey('tracks.id', ondelete='CASCADE'), nullable=False),
    Column('clip_instance_id', String(255), nullable=False),
    Column('clip_id', Integer, nullable=False),  # References clips.clip_id, not clips.id
    Column('start_bar', Integer, nullable=False),
    Column('length_bars', Integer, nullable=False),
    Index('idx_clip_instances_clip_id', 'clip_id')
)

bar_overrides = Table(
    'bar_overrides',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('clip_instance_id', Integer, ForeignKey('clip_instances.id', ondelete='CASCADE'), nullable=False),
    Column('bar_index', Integer, nullable=False),
    Column('velocity_curve', JSON, nullable=True),
    Column('cc_lanes', JSON, nullable=True),
    Column('pitch_bend_curve', JSON, nullable=True),
    Column('aftertouch_curve', JSON, nullable=True),
    Column('pedal_events', JSON, nullable=True),
    Column('metadata', JSON, nullable=True)
)

loops = Table(
    'loops',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('project_id', Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
    Column('start_bar', Integer, nullable=False),
    Column('length_bars', Integer, nullable=False),
    Column('repeat_count', Integer, nullable=False)
)