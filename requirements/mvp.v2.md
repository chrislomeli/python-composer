
# Music Composition Engine – Master Spec (v1.0)
## Overview

This system is designed to create tools for AI agents to create midi input from symbolic input.  The output would be a composition that can be loaded, refined, and played back in a DAW.

- Store musical clips (short sequences of notes) in a database.
- Assemble clips into compositions with multiple tracks.
- Represent musical events with fine-grained MIDI control (velocity, CCs, pitch bend, etc.).
- Support a simple SML language for users and an intermediate DSL language for defining music - - this will be rendered to midi
- Provide an MVP that can be extended with qualitative dynamics and orchestral expression later.

## Work in progress
THE PROJECT HAS DIVERGED over time.  Now we want to pull the following into a cohesive working example that will take SML as input and convert it to the DSL 'language' and then use the DSL to populate the database.
In this step, the user will provide SML (simple markup language) information about the composition.  The tool will then convert this into a composition that can be loaded into the database.

Develop the toolset to support user and langgraph Agentic interactions for taking input as SML information from the user and generating data in the database.
User interaction will happen in two steps:
    * create reusable clips of notes in bars
    * assemble clips from the database into compositions with multiple tracks

These functions need to be complete and work together to produce a composition that can be loaded into the database.
- `pydantic models` definition (src/mvp-changes/schema/models.py)
- `database schema` definition (src/mvp-changes/schema/schema.py)
- `DSL`             definition (src/mvp-changes/dsl/DSL.md)
- `AST`             definition (src/mvp-changes/sml/sml_ast.py)


## Data Models
### 2.1 Note
```python
from pydantic import BaseModel
from typing import Optional, Dict

class Note(BaseModel):
    absolute_pitch: int               # MIDI pitch number (0–127)
    start: float                      # Start time in beats
    duration: float                   # Duration in beats
    is_rest: bool = False
    scale_degree: Optional[int] = None            # Contextual musical semantics
    interval_from_prev: Optional[int] = None      # Melodic shape
    cents_offset: Optional[float] = 0            # Microtonal adjustment
    articulation: Optional[str] = None           # e.g., "detache", "staccato"
    dynamics: Optional[Dict] = None              # e.g., {"velocity": 72}
    expression: Optional[Dict] = None            # CC, pitch bend, aftertouch, pedal events
```




### 2.2 ClipBar

Represents a single bar of a clip, including MIDI expression curves.
```python
from typing import List, Dict, Optional
from pydantic import BaseModel

class ClipBar(BaseModel):
    id: Optional[int] = None
    clip_id: int
    bar_index: int
    velocity_curve: Optional[List[Dict]] = None      # [{"time":0, "value":90}, ...]
    cc: Optional[Dict[int, List[Dict]]] = None       # CC number → events [{"time":0,"value":64}, ...]
    pitch_bend_curve: Optional[List[Dict]] = None    # [{"time":0,"value":0}, {"time":4,"value":200}]
    aftertouch_curve: Optional[List[Dict]] = None
    pedal_events: Optional[List[Dict]] = None
    metadata: Optional[Dict] = None
```

### 2.3 Clip
```python
from typing import List, Optional
from pydantic import BaseModel

class Clip(BaseModel):
    id: Optional[int] = None
    name: str
    track_name: Optional[str] = None
    bars: List[ClipBar] = []
```

### 2.4 Track
```python
from typing import List
from pydantic import BaseModel

class TrackBarRef(BaseModel):
    bar_index: int
    clip: Clip

class Track(BaseModel):
    id: int
    name: str
    bars: List[TrackBarRef]
```


### 2.5 Composition
```python
from typing import List
from pydantic import BaseModel

class Composition(BaseModel):
    id: int
    name: str
    ticks_per_quarter: int
    tempo_bpm: int
    tracks: List[Track]
```

## 3. Database Schema (SQLAlchemy / PostgreSQL)
```
3.1 Notes Table
from sqlalchemy import Table, Column, Integer, Float, Boolean, ForeignKey, MetaData, Index

metadata = MetaData()

notes = Table(
    'notes',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('clip_bar_id', Integer, ForeignKey('clip_bars.id', ondelete='CASCADE'), nullable=False),
    Column('pitch', Integer, nullable=True),
    Column('start_beat', Float, nullable=False),
    Column('duration_beats', Float, nullable=False),
    Column('is_rest', Boolean, default=False),
    Index('idx_notes_clip_bar_id', 'clip_bar_id')
)

# 3.2 Clip Bars Table
from sqlalchemy import JSON, String

clip_bars = Table(
    'clip_bars',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('clip_id', Integer, ForeignKey('clips.id', ondelete='CASCADE'), nullable=False),
    Column('bar_index', Integer, nullable=False),
    Column('velocity_curve', JSON),
    Column('cc', JSON),
    Column('pitch_bend_curve', JSON),
    Column('aftertouch_curve', JSON),
    Column('pedal_events', JSON),
    Column('metadata', JSON)
)

# 3.3 Clips Table
clips = Table(
    'clips',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', String, nullable=False),
    Column('track_name', String, nullable=True)
)

# 3.4 Tracks & TrackBars Table
tracks = Table(
    'tracks',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('composition_id', Integer, ForeignKey('compositions.id', ondelete='CASCADE')),
    Column('name', String, nullable=False)
)

track_bars = Table(
    'track_bars',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('track_id', Integer, ForeignKey('tracks.id', ondelete='CASCADE')),
    Column('bar_index', Integer, nullable=False),
    Column('clip_id', Integer, ForeignKey('clips.id', ondelete='CASCADE')),
    Column('clip_bar_index', Integer, nullable=False)
)

# 3.5 Compositions Table
compositions = Table(
    'compositions',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', String, nullable=False),
    Column('ticks_per_quarter', Integer, nullable=False, default=480),
    Column('tempo_bpm', Integer, nullable=False, default=120)
)
```


## 4. DSL / SMIL → AST Concepts

DSL: A structured JSON representation of compositions and clips.

SMIL: Abstract notation mapping natural language instructions to Note objects and Clip structures.

AST: Represents the composition programmatically for manipulation, validation, and AI-driven transformations.

Example AST Node Structure:

class ASTNode(BaseModel):
    type: str             # "note", "clip", "track", "composition"
    children: list        # Nested nodes
    attributes: dict      # Node-specific attributes

5. MVP Capabilities

Load clips (notes + rests) into the database.

Create compositions using multiple tracks and clips.

Attach MIDI expressions (velocity, CC, pitch bend, aftertouch, pedal) at the ClipBar level.

Query a composition and render as a list of Note objects for MIDI export.

Support loops and repeated sections.

6. Future Extensions

AI / Agent Integration

Use DSL or AST to instruct agents to:

Generate new clips from English prompts

Transform MIDI expressions qualitatively

Orchestral / Section-Level Dynamics

Swells, crescendos, tempo automation

Enhanced Note Semantics

Scale degrees, interval shapes, microtonal expression

Advanced MIDI Export

Multi-channel, VST-targeted tracks, real-time automation

This spec should now serve as the canonical reference for all future development.

We can use it as the single source of truth for Pydantic models, SQLAlchemy tables, DSL/AST design, and agentic workflows.

