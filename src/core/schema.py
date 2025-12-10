# schema.py
from sqlalchemy import (
    Table, Column, Integer, String, Float, Boolean,
    JSON, ForeignKey, MetaData, Index
)

metadata = MetaData()

# ---------------------------------------------------------
# 3.3 CLIPS TABLE (Spec §3.3)
# ---------------------------------------------------------

clips = Table(
    "clips",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(255), nullable=False),
    Column("track_name", String(255), nullable=True),
    Column("tags", JSON, nullable=True),
)

# ---------------------------------------------------------
# 3.2 CLIP BARS TABLE (Spec §3.2)
# ---------------------------------------------------------

clip_bars = Table(
    "clip_bars",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("clip_id", Integer, ForeignKey("clips.id", ondelete="CASCADE"), nullable=False),
    Column("bar_index", Integer, nullable=False),
    
    # Bar-level MIDI expression curves (stored as JSON)
    Column("velocity_curve", JSON, nullable=True),
    Column("cc", JSON, nullable=True),
    Column("pitch_bend_curve", JSON, nullable=True),
    Column("aftertouch_curve", JSON, nullable=True),
    Column("pedal_events", JSON, nullable=True),
    Column("metadata", JSON, nullable=True),
    
    Index("idx_clip_bars_clip_id", "clip_id"),
)

# ---------------------------------------------------------
# 3.1 NOTES TABLE (Spec §3.1)
# ---------------------------------------------------------

notes = Table(
    "notes",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("clip_bar_id", Integer, ForeignKey("clip_bars.id", ondelete="CASCADE"), nullable=False),
    
    # Core MIDI layer
    Column("pitch", Integer, nullable=True),           # MIDI pitch (0-127), None if rest
    Column("start_beat", Float, nullable=False),       # Start time in beats
    Column("duration_beats", Float, nullable=False),   # Duration in beats
    Column("is_rest", Boolean, default=False),
    
    # Contextual musical semantics
    Column("scale_degree", Integer, nullable=True),
    Column("interval_from_prev", Integer, nullable=True),
    Column("cents_offset", Float, nullable=True),
    
    # Articulation and dynamics
    Column("articulation", String(128), nullable=True),
    Column("dynamics", JSON, nullable=True),           # e.g., {"velocity": 72}
    
    # Expression (note-level CC, pitch bend, etc.)
    Column("expression", JSON, nullable=True),
    
    Index("idx_notes_clip_bar_id", "clip_bar_id"),
)

# ---------------------------------------------------------
# 3.5 COMPOSITIONS TABLE (Spec §3.5)
# ---------------------------------------------------------

compositions = Table(
    "compositions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(255), nullable=False),
    Column("ticks_per_quarter", Integer, nullable=False, default=480),
    Column("tempo_bpm", Integer, nullable=False, default=120),
)

# ---------------------------------------------------------
# 3.4 TRACKS TABLE (Spec §3.4)
# ---------------------------------------------------------

tracks = Table(
    "tracks",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("composition_id", Integer, ForeignKey("compositions.id", ondelete="CASCADE"), nullable=False),
    Column("name", String(255), nullable=False),
    
    Index("idx_tracks_composition_id", "composition_id"),
)

# ---------------------------------------------------------
# 3.4 TRACK BARS TABLE (Spec §3.4)
# ---------------------------------------------------------

track_bars = Table(
    "track_bars",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("track_id", Integer, ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False),
    Column("bar_index", Integer, nullable=False),
    Column("clip_id", Integer, ForeignKey("clips.id", ondelete="CASCADE"), nullable=False),
    Column("clip_bar_index", Integer, nullable=False),
    
    Index("idx_track_bars_track_id", "track_id"),
)
