# sml_ast.py
# AST models for SMIL → DSL → Database pipeline
# Aligned with spec §2.1-2.5 and updated Pydantic models

from __future__ import annotations
from typing import Optional, List, Dict, Union, Any
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError
import re
import math

# ----------------------------
# Configuration / Constants
# ----------------------------
DEFAULT_UNITS_PER_BAR = 32   # matches earlier convention (8 units per quarter in 4/4)
DURATION_UNIT_MAP = {
    "whole": 32,
    "half": 16,
    "quarter": 8,
    "eighth": 4,
    "sixteenth": 2,
    "thirty_second": 1,
    # dotted variants computed via 1.5 * base; triplets via 2/3 * base
    "dotted_half": int(round(16 * 1.5)),
    "dotted_quarter": int(round(8 * 1.5)),
    "dotted_eighth": int(round(4 * 1.5)),
    "triplet_quarter": int(round(8 * 2 / 3)),
    "triplet_eighth": int(round(4 * 2 / 3)),
    "triplet_sixteenth": int(round(2 * 2 / 3)),
}

PITCH_REGEX = re.compile(r'^([A-Ga-g])([#b♯♭]?)(-?\d+)$')

# ----------------------------
# Primitive / utility types
# ----------------------------

class CurvePoint(BaseModel):
    """A point in a CC/pitch-bend/expression curve (time in beats)."""
    time: float
    value: float

class ExpressionModel(BaseModel):
    """Per-note expressive data (note-level only)."""
    extra: Optional[Dict[str, Any]] = None


class BarExpressionModel(BaseModel):
    """Bar-level expression curves (velocity, CC, pitch bend, etc.)."""
    velocity_curve: Optional[List[Dict]] = None      # [{"time":0, "value":90}, ...]
    cc: Optional[Dict[int, List[Dict]]] = None       # CC number → events
    pitch_bend_curve: Optional[List[Dict]] = None
    aftertouch_curve: Optional[List[Dict]] = None
    pedal_events: Optional[List[Dict]] = None
    metadata: Optional[Dict] = None

# ----------------------------
# Musical primitives
# ----------------------------
class Pitch(BaseModel):
    """Represent a pitch in both name+octave form and as MIDI number."""
    name: Optional[str] = None   # e.g. "C", "C#", "Db"
    octave: Optional[int] = None
    midi: Optional[int] = None

    @classmethod
    def from_string(cls, s: str) -> "Pitch":
        """
        Parse strings like "C4", "C#4", "Db3", "A-1".
        Returns Pitch with midi computed.
        """
        m = PITCH_REGEX.match(s.strip())
        if not m:
            raise ValueError(f"Invalid pitch string: {s}")
        letter, accidental, oct_str = m.groups()
        letter = letter.upper()
        accidental = accidental.replace('♯', '#').replace('♭', 'b')
        octave = int(oct_str)
        # base semitone mapping for natural notes relative to C
        base_map = {"C":0,"D":2,"E":4,"F":5,"G":7,"A":9,"B":11}
        if letter not in base_map:
            raise ValueError(f"Invalid pitch letter: {letter}")
        semitone = base_map[letter]
        if accidental == '#' :
            semitone += 1
        elif accidental == 'b':
            semitone -= 1
        # midi calculation: MIDI note 0 = C-1 (octave -1), so midi = (octave + 1) * 12 + semitone
        midi = (octave + 1) * 12 + semitone
        if midi < 0 or midi > 127:
            raise ValueError(f"Resulting MIDI {midi} out of range for pitch '{s}'")
        return cls(name=f"{letter}{accidental}" if accidental else letter, octave=octave, midi=midi)

    @classmethod
    def from_midi(cls, midi: int) -> "Pitch":
        if midi < 0 or midi > 127:
            raise ValueError("midi out of range")
        octave = (midi // 12) - 1
        semitone = midi % 12
        rev_map = {0:"C",1:"C#",2:"D",3:"D#",4:"E",5:"F",6:"F#",7:"G",8:"G#",9:"A",10:"A#",11:"B"}
        name = rev_map[semitone]
        return cls(name=name, octave=octave, midi=midi)

# ----------------------------
# Duration / timing helpers
# ----------------------------
class DurationSpec(BaseModel):
    """Represent duration in named form (e.g., 'quarter') and computed units for a given units_per_bar."""
    name: str
    units_per_bar: int = Field(default=DEFAULT_UNITS_PER_BAR)
    units: int = 0

    @model_validator(mode="after")
    def compute_units(self):
        key = self.name
        if key in DURATION_UNIT_MAP:
            base = DURATION_UNIT_MAP[key]
        else:
            # allow numeric specification like "units:4" by using name as integer string
            try:
                base = int(key)
            except Exception:
                raise ValueError(f"Unknown duration token: {key}")
        # scale if the engine uses different units_per_bar than 32
        # base is expressed in units where 32==whole. If units_per_bar != 32, scale linearly.
        scale = self.units_per_bar / DEFAULT_UNITS_PER_BAR
        self.units = max(1, int(round(base * scale)))
        return self

# ----------------------------
# Bar Items (Note or Rest)
# ----------------------------
class NoteItem(BaseModel):
    pitch: Pitch
    duration: DurationSpec
    velocity: Optional[int] = Field(default=90, ge=0, le=127)
    articulation: Optional[str] = "normal"
    tie: Optional[str] = None  # "start", "stop", "continue"
    expression: Optional[ExpressionModel] = None

    # These get filled when computing bar layout:
    start_unit: Optional[int] = None
    duration_units: Optional[int] = None

    @model_validator(mode="after")
    def validate_pitch_and_duration(self):
        if self.pitch is None or self.pitch.midi is None:
            raise ValueError("NoteItem requires a valid Pitch with midi value")
        # ensure duration.units computed
        if self.duration.units <= 0:
            raise ValueError("Computed duration units must be positive")
        return self

    def to_spec_note(self, units_per_beat: float = 8.0) -> Dict[str, Any]:
        """Return a dict matching spec §2.1 Note model (absolute_pitch, start, duration in beats)."""
        if self.start_unit is None or self.duration.units is None:
            raise ValueError("start_unit and duration must be computed before conversion")
        
        # Convert units to beats (assuming units_per_beat = 8 for quarter notes)
        start_beats = self.start_unit / units_per_beat
        duration_beats = self.duration.units / units_per_beat
        
        return {
            "absolute_pitch": self.pitch.midi,
            "start": start_beats,
            "duration": duration_beats,
            "is_rest": False,
            "scale_degree": None,
            "interval_from_prev": None,
            "cents_offset": 0.0,
            "articulation": self.articulation,
            "dynamics": {"velocity": self.velocity} if self.velocity else None,
            "expression": self.expression.model_dump() if self.expression else None
        }

class RestItem(BaseModel):
    duration: DurationSpec
    start_unit: Optional[int] = None
    duration_units: Optional[int] = None

    @model_validator(mode="after")
    def validate_duration(self):
        if self.duration.units <= 0:
            raise ValueError("Rest must have positive duration")
        return self

    def to_spec_rest(self, units_per_beat: float = 8.0) -> Dict[str, Any]:
        """Return a dict matching spec §2.1 Note model for rests."""
        if self.start_unit is None or self.duration.units is None:
            raise ValueError("start_unit and duration must be computed before conversion")
        
        start_beats = self.start_unit / units_per_beat
        duration_beats = self.duration.units / units_per_beat
        
        return {
            "absolute_pitch": 0,  # Placeholder for rest
            "start": start_beats,
            "duration": duration_beats,
            "is_rest": True,
            "scale_degree": None,
            "interval_from_prev": None,
            "cents_offset": 0.0,
            "articulation": None,
            "dynamics": None,
            "expression": None
        }

BarItem = Union[NoteItem, RestItem]

# ----------------------------
# Bar, Clip, Track, Composition AST nodes
# ----------------------------
class Bar(BaseModel):
    number: Optional[int] = None  # bar index within a clip or composition (1-based)
    items: List[BarItem]
    units_per_bar: int = Field(default=DEFAULT_UNITS_PER_BAR)

    @model_validator(mode="after")
    def normalize_items(self):
        # Ensure DurationSpec objects know units_per_bar
        for it in self.items:
            # Pydantic will coerce dicts to proper models; ensure types
            if isinstance(it, NoteItem):
                it.duration.units_per_bar = self.units_per_bar
                it.duration = DurationSpec.model_validate(it.duration)
            elif isinstance(it, RestItem):
                it.duration.units_per_bar = self.units_per_bar
                it.duration = DurationSpec.model_validate(it.duration)
        return self

    def layout(self):
        """
        Compute start_unit and duration_units for each item by accumulating durations.
        Validates that total units <= units_per_bar.
        """
        cursor = 0
        for it in self.items:
            # compute units (already scaled by DurationSpec)
            dur_units = it.duration.units
            if isinstance(it, NoteItem):
                it.start_unit = cursor
                it.duration_units = dur_units
            else:
                it.start_unit = cursor
                it.duration_units = dur_units
            cursor += dur_units
        if cursor > self.units_per_bar:
            raise ValueError(f"Bar overflow: total units {cursor} > units_per_bar {self.units_per_bar}")
        return self

    def to_spec_notes(self, units_per_beat: float = 8.0) -> List[Dict[str, Any]]:
        """Return a list of spec-compliant Note representations (§2.1)."""
        self.layout()
        out = []
        for it in self.items:
            if isinstance(it, NoteItem):
                out.append(it.to_spec_note(units_per_beat))
            else:
                out.append(it.to_spec_rest(units_per_beat))
        return out

class ClipBar(BaseModel):
    """AST representation of a ClipBar (matches spec §2.2)."""
    bar_index: int
    items: List[BarItem] = Field(default_factory=list)
    units_per_bar: int = Field(default=DEFAULT_UNITS_PER_BAR)
    
    # Bar-level expression curves
    expression: Optional[BarExpressionModel] = None
    
    def layout(self):
        """Compute start_unit and duration_units for each item."""
        cursor = 0
        for it in self.items:
            dur_units = it.duration.units
            if isinstance(it, NoteItem):
                it.start_unit = cursor
                it.duration_units = dur_units
            else:
                it.start_unit = cursor
                it.duration_units = dur_units
            cursor += dur_units
        if cursor > self.units_per_bar:
            raise ValueError(f"Bar overflow: total units {cursor} > units_per_bar {self.units_per_bar}")
        return self
    
    def to_spec_clipbar(self, clip_id: int, units_per_beat: float = 8.0) -> Dict[str, Any]:
        """Return dict matching spec §2.2 ClipBar model."""
        self.layout()
        notes = []
        for it in self.items:
            if isinstance(it, NoteItem):
                notes.append(it.to_spec_note(units_per_beat))
            else:
                notes.append(it.to_spec_rest(units_per_beat))
        
        result = {
            "clip_id": clip_id,
            "bar_index": self.bar_index,
            "notes": notes
        }
        
        # Add bar-level expression curves if present
        if self.expression:
            expr_dict = self.expression.model_dump(exclude_none=True)
            result.update(expr_dict)
        
        return result


class Clip(BaseModel):
    """AST representation of a Clip (matches spec §2.3)."""
    clip_id: Optional[int] = None
    name: Optional[str] = None
    track_name: Optional[str] = None
    bars: List[ClipBar] = Field(default_factory=list)

    def validate_and_layout(self):
        for b in self.bars:
            b.units_per_bar = DEFAULT_UNITS_PER_BAR
            b.layout()
        return self

    def to_spec_clip(self, units_per_beat: float = 8.0) -> Dict[str, Any]:
        """Return dictionary matching spec §2.3 Clip model."""
        self.validate_and_layout()
        clip_bars = []
        for b in self.bars:
            clip_bars.append(b.to_spec_clipbar(self.clip_id or 0, units_per_beat))
        
        return {
            "id": self.clip_id,
            "name": self.name,
            "track_name": self.track_name,
            "bars": clip_bars
        }

class TrackBarRef(BaseModel):
    """AST representation of TrackBarRef (matches spec §2.4)."""
    bar_index: int
    clip_id: int
    clip_bar_index: int

class Track(BaseModel):
    """AST representation of Track (matches spec §2.4)."""
    id: Optional[int] = None
    name: str
    bars: List[TrackBarRef] = Field(default_factory=list)
    
    def to_spec_track(self) -> Dict[str, Any]:
        """Return dictionary matching spec §2.4 Track model."""
        return {
            "id": self.id,
            "name": self.name,
            "bars": [bar.model_dump() for bar in self.bars]
        }

class LoopSpec(BaseModel):
    start_bar: int
    length_bars: int
    repeat_count: int = 1

class Composition(BaseModel):
    """AST representation of Composition (matches spec §2.5)."""
    id: Optional[int] = None
    name: str
    ticks_per_quarter: int = 480
    tempo_bpm: int = 120
    tracks: List[Track] = Field(default_factory=list)
    
    # Extended metadata (not in core spec but useful for DSL)
    tempo_map: Optional[List[Dict[str, Any]]] = None
    meter_map: Optional[List[Dict[str, Any]]] = None
    key_map: Optional[List[Dict[str, Any]]] = None
    loops: Optional[List[LoopSpec]] = None

    def to_spec_composition(self) -> Dict[str, Any]:
        """Return dictionary matching spec §2.5 Composition model."""
        return {
            "id": self.id,
            "name": self.name,
            "ticks_per_quarter": self.ticks_per_quarter,
            "tempo_bpm": self.tempo_bpm,
            "tracks": [t.to_spec_track() for t in self.tracks]
        }

# ----------------------------
# Convenience parsers & helpers
# ----------------------------
def smil_bar_from_dict(d: Dict[str, Any], units_per_bar: int = DEFAULT_UNITS_PER_BAR) -> ClipBar:
    """
    Convert a SMIL-like dict to AST ClipBar.
    Expected format:
      {"bar_index": 1, "items": [
           {"note": "C4", "duration": "quarter"},
           {"rest": "quarter"}
       ],
       "expression": {"velocity_curve": [...], ...}
      }
    """
    bar_index = d.get("bar_index", d.get("number", 1))
    raw_items = d.get("items", [])
    items: List[BarItem] = []
    
    for it in raw_items:
        if "note" in it:
            pitch_str = it["note"]
            pitch = Pitch.from_string(pitch_str)
            duration_name = it.get("duration")
            dur = DurationSpec(name=duration_name, units_per_bar=units_per_bar)
            velocity = it.get("velocity", 90)
            art = it.get("articulation", "normal")
            expr = None
            if "expression" in it and it["expression"] is not None:
                expr = ExpressionModel.model_validate(it["expression"])
            items.append(NoteItem(pitch=pitch, duration=dur, velocity=velocity, articulation=art, expression=expr))
        elif "rest" in it:
            duration_name = it["rest"]
            dur = DurationSpec(name=duration_name, units_per_bar=units_per_bar)
            items.append(RestItem(duration=dur))
        else:
            raise ValueError(f"Unknown bar item: {it}")
    
    # Parse bar-level expression if present
    bar_expr = None
    if "expression" in d and d["expression"]:
        bar_expr = BarExpressionModel.model_validate(d["expression"])
    
    return ClipBar(bar_index=bar_index, items=items, units_per_bar=units_per_bar, expression=bar_expr)

def clip_from_smil_dict(d: Dict[str, Any], units_per_bar: int = DEFAULT_UNITS_PER_BAR) -> Clip:
    """
    Convert a SMIL-like clip dict to AST Clip (spec-compliant).
    Expected SMIL clip format:
    {
      "clip_id": 8,
      "name": "lead-riff",
      "track_name": "lead",
      "bars": [ <bar dicts> ]
    }
    """
    bars_raw = d.get("bars", [])
    bars = []
    for br in bars_raw:
        bar = smil_bar_from_dict(br, units_per_bar=units_per_bar)
        bars.append(bar)
    return Clip(
        clip_id=d.get("clip_id"),
        name=d.get("name"),
        track_name=d.get("track_name"),
        bars=bars
    )


def composition_from_smil_dict(d: Dict[str, Any]) -> Composition:
    """Convert an SML-style project dict into a Composition AST.

    This is a minimal composition syntax for the MVP, assuming that clips are
    already stored in the database and referenced by clip_id. Expected format:

    {
      "project": {
        "name": "my-song",
        "ticks_per_quarter": 480,
        "tempo_map": [
          {"bar": 1, "tempo_bpm": 120}
        ],
        "meter_map": [...],
        "key_map":   [...],
        "tracks": {
          "lead": {
            "clips": [
              {
                "clip_instance_id": "lead_1",
                "clip_id": 8,
                "start_bar": 1,
                "length_bars": 2
              }
            ]
          }
        },
        "loops": [
          {"start_bar": 1, "length_bars": 4, "repeat_count": 2}
        ]
      }
    }
    """

    # Accept either top-level project or wrapped under "project"
    project = d.get("project", d)

    name = project.get("name", "Untitled")
    ticks_per_quarter = project.get("ticks_per_quarter", 480)

    tempo_map = project.get("tempo_map")
    meter_map = project.get("meter_map")
    key_map = project.get("key_map")

    tempo_bpm = 120
    if tempo_map and len(tempo_map) > 0:
        tempo_bpm = int(tempo_map[0].get("tempo_bpm", 120))

    # Build Track AST nodes from track definitions
    tracks_ast: List[Track] = []
    tracks_def: Dict[str, Any] = project.get("tracks", {})

    for track_name, track_data in tracks_def.items():
        clips_def = track_data.get("clips", [])
        bar_refs: List[TrackBarRef] = []

        for clip_inst in clips_def:
            clip_id = clip_inst.get("clip_id")
            if clip_id is None:
                raise ValueError("SML track clip instance must include 'clip_id'")

            start_bar = int(clip_inst.get("start_bar", 1))
            length_bars = int(clip_inst.get("length_bars", 1))

            # For this MVP, we assume the first N bars of the clip are used
            # in order, and length_bars tells us how many. The user is
            # responsible for ensuring that the clip has at least that many
            # bars stored in the database.
            for i in range(length_bars):
                bar_index = start_bar + i
                clip_bar_index = i  # 0-based index into the clip's bars

                bar_refs.append(
                    TrackBarRef(
                        bar_index=bar_index,
                        clip_id=clip_id,
                        clip_bar_index=clip_bar_index,
                    )
                )

        tracks_ast.append(Track(name=track_name, bars=bar_refs))

    # Optional loops metadata
    loops_ast: Optional[List[LoopSpec]] = None
    loops_def = project.get("loops")
    if loops_def is not None:
        loops_ast = [LoopSpec(**ld) for ld in loops_def]

    return Composition(
        name=name,
        ticks_per_quarter=ticks_per_quarter,
        tempo_bpm=tempo_bpm,
        tracks=tracks_ast,
        tempo_map=tempo_map,
        meter_map=meter_map,
        key_map=key_map,
        loops=loops_ast,
    )

# ----------------------------
# Example usage (for interactive testing)
# ----------------------------
if __name__ == "__main__":
    # Example SMIL bar dict
    smil_bar = {
        "bar_index": 1,
        "items": [
            {"note": "C4", "duration": "quarter"},
            {"note": "E4", "duration": "quarter"},
            {"note": "G3", "duration": "quarter"},
            {"rest": "quarter"}
        ],
        "expression": {
            "velocity_curve": [{"time": 0, "value": 90}, {"time": 4, "value": 100}]
        }
    }

    clip_smil = {
        "clip_id": 8,
        "name": "lead-riff-intro",
        "track_name": "lead",
        "bars": [
            smil_bar,
            {
                "bar_index": 2,
                "items": [
                    {"note": "D4", "duration": "quarter"},
                    {"note": "F4", "duration": "quarter"},
                    {"note": "A4", "duration": "quarter"},
                    {"rest": "quarter"}
                ]
            }
        ]
    }

    try:
        clip = clip_from_smil_dict(clip_smil)
        clip.validate_and_layout()
        print("Clip -> Spec-compliant structure:")
        import json
        print(json.dumps(clip.to_spec_clip(), indent=2))
    except ValidationError as e:
        print("Validation error:", e)
