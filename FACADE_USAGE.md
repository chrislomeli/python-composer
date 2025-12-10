# OSC Facade Usage Guide

## Overview

The `OSCFacade` provides a high-level Pydantic-based interface for working with DSL, database, and MIDI operations.

## Features Implemented

### 1. SML to DSL Conversion
Convert SML/SMIL format to spec-compliant DSL format (proxies through `sml_ast.py`).

### 2. Load DSL into Database
Load any DSL JSON file or dict into the database, creating clips and compositions.

### 3. Search Clips by Tags
Retrieve clips by tag search and return valid DSL format.

### 4. Export Composition to DSL
Retrieve a whole composition from database by ID and return complete DSL project.

## Usage Examples

### Setup

```python
from src.controller.osc_facade import (
    OSCFacade,
    DSLLoadConfig,
    ClipSearchRequest,
    DSLProjectModel
)

# Initialize facade
facade = OSCFacade()
```

### 1. Convert SML/SMIL to DSL

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

### 2. Load DSL from File

```python
# Load from file path
config = DSLLoadConfig(path="src/dsl/examples/02-multi-track.json")
result = await facade.load_dsl_to_db(config)

print(f"Loaded composition: {result.composition_name}")
print(f"Composition ID: {result.composition_id}")
print(f"Created {len(result.clip_ids)} clips: {result.clip_ids}")
```

### 3. Load DSL from Dict

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

### 4. Search Clips by Tags

```python
# Search by tags
request = ClipSearchRequest(tags=["verse", "melody"])
response = await facade.search_clips(request)

for clip in response.clips:
    print(f"Found clip: {clip['name']}")
    print(f"  Tags: {clip.get('tags', [])}")
    print(f"  Notes: {len(clip['notes'])}")
```

### 5. Search Clips by Name Pattern

```python
# Search by name pattern (SQL LIKE syntax)
request = ClipSearchRequest(name_pattern="%melody%")
response = await facade.search_clips(request)

for clip in response.clips:
    print(f"Found clip: {clip['name']}")
```

### 6. Get Single Clip as DSL

```python
# Get specific clip by ID
clip_dsl = await facade.clip_to_dsl(clip_id=1)

print(f"Clip: {clip_dsl['name']}")
print(f"Notes: {clip_dsl['notes']}")
```

### 7. Export Composition to DSL

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

### 8. Complete Workflow: Load, Search, Export

```python
import asyncio

async def complete_workflow():
    facade = OSCFacade()
    
    # 1. Load DSL into database
    print("Loading DSL...")
    config = DSLLoadConfig(path="src/dsl/examples/02-multi-track.json")
    load_result = await facade.load_dsl_to_db(config)
    print(f"✓ Loaded composition {load_result.composition_id}")
    
    # 2. Search for clips by tag
    print("\nSearching for clips with 'melody' tag...")
    search_request = ClipSearchRequest(tags=["melody"])
    search_result = await facade.search_clips(search_request)
    print(f"✓ Found {len(search_result.clips)} clips")
    
    # 3. Export composition back to DSL
    print("\nExporting composition to DSL...")
    dsl_project = await facade.composition_to_dsl(load_result.composition_id)
    print(f"✓ Exported: {dsl_project.project['name']}")
    print(f"  Tracks: {len(dsl_project.project['tracks'])}")
    print(f"  Clips: {len(dsl_project.project['clip_library'])}")
    
    return dsl_project

# Run the workflow
if __name__ == "__main__":
    result = asyncio.run(complete_workflow())
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
