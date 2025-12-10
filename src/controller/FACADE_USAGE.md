# OSC Facade Usage Guide

## Overview

The `OSCFacade` provides a high-level Pydantic-based interface for working with DSL, database, and MIDI operations.

## Features Implemented

### 1. Natural Language to SML (LangGraph)
Convert natural language prompts to SML clip format using LangGraph + OpenAI (proxies through `clip_graph.py`).

### 2. SML to DSL Conversion
Convert SML/SMIL format to spec-compliant DSL format (proxies through `sml_ast.py`).

### 3. Load DSL into Database
Load any DSL JSON file or dict into the database, creating clips and compositions.

### 4. Search Clips by Tags
Retrieve clips by tag search and return valid DSL format.

### 5. Export Composition to DSL
Retrieve a whole composition from database by ID and return complete DSL project.

### 6. Complete NL → DB Pipeline
One-step natural language clip generation directly to database.

### 7. Playback Workflows
Preview clips before storing to database (SML → DSL → Play).

## Usage Examples

### Setup

```python
from src.controller.osc_facade import (
    OSCFacade,
    DSLLoadConfig,
    ClipSearchRequest,
    DSLProjectModel,
    NLToSMLRequest,
    PlaybackConfig
)

# Initialize facade
facade = OSCFacade()
```

### 1. Natural Language to SML (LangGraph)

```python
# Generate SML clip from natural language using LangGraph + OpenAI
# Requires: OPENAI_API_KEY environment variable

from src.controller.osc_facade import NLToSMLRequest

request = NLToSMLRequest(text="Create a 2-bar ascending C major scale, quarter notes")
sml_response = await facade.natural_language_clip_to_sml(request)

print(f"Generated SML clip: {sml_response.sml['name']}")
print(f"Bars: {len(sml_response.sml['bars'])}")

# The SML can then be converted to DSL or stored directly
dsl_clip = facade.sml_to_dsl_clip(sml_response.sml)
```

### 2. Rapid Iteration Workflow: NL → Play (Preview Before Storing)

```python
# The main workflow: Generate and play immediately, store only if you like it
# Requires: OPENAI_API_KEY and a SoundFont file

request = NLToSMLRequest(text="Create a jazzy bass line in F, 4 bars, eighth notes")
config = PlaybackConfig(
    sf2_path="FluidR3_GM.sf2",  # Path to your SoundFont
    bpm=120,
    loop=False
)

# Generate, play, and get the SML back
sml_response = await facade.play_clip_from_nl(request, config)

print(f"Played clip: {sml_response.sml['name']}")

# If you like it, store it to database:
dsl_clip = facade.sml_to_dsl_clip(sml_response.sml)
clip_id = await facade.clip_service.create_clip_from_dsl(dsl_clip)
print(f"Stored with ID: {clip_id}")
```

### 3. Play Clip from SML (Without NL Generation)

```python
# If you already have SML (e.g., from a file or manual creation)
sml_clip = {
    "name": "my-riff",
    "bars": [
        {
            "bar_index": 0,
            "items": [
                {"note": "C4", "duration": "quarter"},
                {"note": "E4", "duration": "quarter"},
                {"note": "G4", "duration": "half"}
            ]
        }
    ]
}

config = PlaybackConfig(sf2_path="FluidR3_GM.sf2", bpm=120)
await facade.play_clip_from_sml(sml_clip, config)
```

### 4. Play Clip from Database

```python
# Play a clip that's already stored in the database
config = PlaybackConfig(sf2_path="FluidR3_GM.sf2", bpm=140, loop=True)
await facade.play_clip(clip_id=1, config=config)
```

### 5. Complete NL → DB Pipeline (Store Without Playing)

```python
# Generate clip from natural language and store directly to database
request = NLToSMLRequest(text="Create a C major scale, quarter notes")
clip_id = await facade.natural_language_clip_to_db(request)

print(f"Created clip with ID: {clip_id}")

# Retrieve it back
clip_dsl = await facade.clip_to_dsl(clip_id)
print(f"Clip name: {clip_dsl['name']}")
```

### 6. Convert SML/SMIL to DSL

```python
# Convert SMIL clip to DSL format
sml_clip = {
    "clip_id": 8,
    "name": "lead-riff",
    "track_name": "lead",
    "bars": [
        {
            "bar_index": 0,
            "items": [
                {"note": "C4", "duration": "quarter"},
                {"note": "E4", "duration": "quarter"},
                {"note": "G4", "duration": "quarter"},
                {"rest": "quarter"}
            ],
            "expression": {
                "velocity_curve": [{"time": 0, "value": 90}, {"time": 4, "value": 100}]
            }
        }
    ]
}

# Convert to spec-compliant DSL
dsl_clip = facade.sml_to_dsl_clip(sml_clip)
print(f"Converted clip: {dsl_clip['name']}")
print(f"Bars: {len(dsl_clip['bars'])}")

# Convert SML composition to DSL
sml_project = {
    "project": {
        "name": "my-song",
        "ticks_per_quarter": 480,
        "tempo_map": [{"bar": 1, "tempo_bpm": 120}],
        "meter_map": [{"bar": 1, "numerator": 4, "denominator": 4}],
        "key_map": [{"bar": 1, "key": "C", "mode": "major"}],
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
        }
    }
}

dsl_composition = facade.sml_to_dsl_composition(sml_project)
print(f"Converted composition: {dsl_composition['name']}")
```

### 7. Load DSL from File

```python
# Load from file path
config = DSLLoadConfig(path="../dsl/examples/02-multi-track.json")
result = await facade.load_dsl_to_db(config)

print(f"Loaded composition: {result.composition_name}")
print(f"Composition ID: {result.composition_id}")
print(f"Created {len(result.clip_ids)} clips: {result.clip_ids}")
```

### 8. Load DSL from Dict

```python
dsl_json = {
    "project": {
        "name": "my_song",
        "ticks_per_quarter": 480,
        "tempo_map": [{"bar": 1, "tempo_bpm": 120}],
        "meter_map": [{"bar": 1, "numerator": 4, "denominator": 4}],
        "key_map": [{"bar": 1, "key": "C", "mode": "major"}],
        "tracks": {
            "melody": {
                "instrument": {"name": "piano", "midi_channel": 0},
                "clips": [
                    {
                        "clip_instance_id": "m1",
                        "clip_id": 1,
                        "start_bar": 1,
                        "length_bars": 2
                    }
                ]
            }
        },
        "clip_library": [
            {
                "clip_id": 1,
                "name": "melody-verse",
                "tags": ["verse", "melody", "piano"],
                "notes": [
                    {"pitch": 60, "start_beat": 0.0, "duration_beats": 2.0},
                    {"pitch": 62, "start_beat": 2.0, "duration_beats": 2.0}
                ]
            }
        ]
    }
}

config = DSLLoadConfig(dsl_json=dsl_json)
result = await facade.load_dsl_to_db(config)
```

### 9. Search Clips by Tags

```python
# Search by tags
request = ClipSearchRequest(tags=["verse", "melody"])
response = await facade.search_clips(request)

for clip in response.clips:
    print(f"Found clip: {clip['name']}")
    print(f"  Tags: {clip.get('tags', [])}")
    print(f"  Notes: {len(clip['notes'])}")
```

### 10. Search Clips by Name Pattern

```python
# Search by name pattern (SQL LIKE syntax)
request = ClipSearchRequest(name_pattern="%melody%")
response = await facade.search_clips(request)

for clip in response.clips:
    print(f"Found clip: {clip['name']}")
```

### 11. Get Single Clip as DSL

```python
# Get specific clip by ID
clip_dsl = await facade.clip_to_dsl(clip_id=1)

print(f"Clip: {clip_dsl['name']}")
print(f"Notes: {clip_dsl['notes']}")
```

### 12. Export Composition to DSL

```python
# Export full composition back to DSL format
dsl_project = await facade.composition_to_dsl(composition_id=1)

# Access the project structure
project = dsl_project.project
print(f"Project name: {project['name']}")
print(f"Tracks: {list(project['tracks'].keys())}")
print(f"Clips in library: {len(project['clip_library'])}")

# Save to file
import json
with open("exported_composition.json", "w") as f:
    json.dump({"project": project}, f, indent=2)
```

### 13. Complete Workflow: NL → Play → Store → Export

```python
import asyncio

async def rapid_iteration_workflow():
    """The main workflow: Generate, play, iterate, then store."""
    facade = OSCFacade()
    
    # 1. Generate and play clips from natural language
    print("Generating and playing clips...")
    playback_config = PlaybackConfig(sf2_path="FluidR3_GM.sf2", bpm=120)
    
    # Try different ideas
    ideas = [
        "Create a funky bass line in E, 2 bars",
        "Create a melodic piano riff in C major, 4 bars",
        "Create a drum pattern with kick and snare"
    ]
    
    stored_clips = []
    for idea in ideas:
        print(f"\n🎵 Trying: {idea}")
        request = NLToSMLRequest(text=idea)
        
        # Generate and play
        sml_response = await facade.play_clip_from_nl(request, playback_config)
        
        # Simulate user decision (in real app, this would be user input)
        store_it = True  # User liked it!
        
        if store_it:
            # Store to database
            dsl_clip = facade.sml_to_dsl_clip(sml_response.sml)
            clip_id = await facade.clip_service.create_clip_from_dsl(dsl_clip)
            stored_clips.append(clip_id)
            print(f"✓ Stored clip {clip_id}")
        else:
            print("✗ Discarded")
    
    # 2. Search for stored clips
    print(f"\n📂 Searching for clips...")
    search_request = ClipSearchRequest(tags=["bass", "melody"])
    search_result = await facade.search_clips(search_request)
    print(f"✓ Found {len(search_result.clips)} clips")
    
    # 3. Play a stored clip from database
    if stored_clips:
        print(f"\n▶️  Playing stored clip {stored_clips[0]}...")
        await facade.play_clip(stored_clips[0], playback_config)
    
    # 4. Export to DSL file
    print("\n💾 Exporting clips to DSL...")
    for clip_id in stored_clips:
        dsl_clip = await facade.clip_to_dsl(clip_id)
        filename = f"exported_clip_{clip_id}.json"
        with open(filename, "w") as f:
            json.dump(dsl_clip, f, indent=2)
        print(f"✓ Exported {filename}")

# Run the workflow
if __name__ == "__main__":
    asyncio.run(rapid_iteration_workflow())
```

## Data Models

### DSLLoadConfig
```python
class DSLLoadConfig(BaseModel):
    path: Optional[str] = None          # Path to DSL JSON file
    dsl_json: Optional[Dict[str, Any]] = None  # Or provide dict directly
```

### DSLLoadResult
```python
class DSLLoadResult(BaseModel):
    composition_id: int                 # ID of created composition
    clip_ids: List[int]                 # IDs of created clips
    composition_name: str               # Name of the composition
```

### ClipSearchRequest
```python
class ClipSearchRequest(BaseModel):
    tags: Optional[List[str]] = None           # Search by tags
    name_pattern: Optional[str] = None         # Search by name (SQL LIKE)
```

### ClipDSLResponse
```python
class ClipDSLResponse(BaseModel):
    clips: List[Dict[str, Any]]         # List of clips in DSL format
```

### DSLProjectModel
```python
class DSLProjectModel(BaseModel):
    project: Dict[str, Any]             # Complete DSL project structure
```

### NLToSMLRequest
```python
class NLToSMLRequest(BaseModel):
    text: str                           # Natural language prompt
```

### NLToSMLResponse
```python
class NLToSMLResponse(BaseModel):
    sml: Dict[str, Any]                 # SML-style clip dict
```

### PlaybackConfig
```python
class PlaybackConfig(BaseModel):
    sf2_path: Optional[str] = None      # Path to SoundFont file
    bpm: int = 120                      # Tempo in beats per minute
    loop: bool = False                  # Whether to loop playback
```

## DSL Clip Format

Clips returned from search or export have this structure:

```python
{
    "clip_id": 1,
    "name": "melody-verse",
    "tags": ["verse", "melody"],        # Optional
    "track_name": "melody",             # Optional
    "notes": [
        {
            "pitch": 60,                # MIDI note (or omit for rest)
            "start_beat": 0.0,          # Absolute beat position
            "duration_beats": 2.0,
            "is_rest": False,           # Optional, for rests
            "articulation": "legato",   # Optional
            "dynamics": {"velocity": 80} # Optional
        }
    ]
}
```

## Database Schema Changes

The facade implementation added tag support to clips:

- **clips table**: Added `tags` column (JSON array)
- **Clip model**: Added `tags: Optional[List[str]]` field
- **ClipRepository**: Added `find_by_tags()` method
- **ClipService**: Updated to handle tags in create and search

## Integration with Existing Code

The facade uses existing services:
- `ClipService` - for clip operations
- `CompositionService` - for composition operations
- `DSLParser` - for parsing DSL JSON

All database operations are async and use the existing repository pattern.

## Next Steps

To use this in your application:

1. Initialize the database (if not already done)
2. Create an `OSCFacade` instance
3. Use the async methods to load/search/export DSL

The facade is designed to be the main entry point for DSL operations, abstracting away the complexity of database operations and format conversions.
