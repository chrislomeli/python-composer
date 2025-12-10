# OSC Code Architecture Audit

## Feature Matrix

| Feature                | What it does                                                       | Current implementation                                      | High-level bridge plan |
|------------------------|--------------------------------------------------------------------|-------------------------------------------------------------|-------------------------|
| `natural_language_to_sml` | Convert free text into SML/SMIL structures that describe clips/compositions | **None yet** – planned via LangGraph or similar LLM tooling | Defer; when added, target SML payloads that `clip_from_smil_dict` and `composition_from_smil_dict` already accept |
| `sml_to_dsl`           | Convert SML/SMIL input into the spec/DSL clip & composition dicts used by services | **Partial** – `sml_ast.clip_from_smil_dict` + `Clip.to_spec_clip`, `composition_from_smil_dict` and FastAPI endpoints map SML → DSL-like dicts | Treat these helpers as the canonical SML→DSL path and optionally wrap them in explicit `sml_to_dsl_clip` / `sml_to_dsl_composition` functions for clarity |
| `store_dsl_to_db`      | Take a DSL project (or DSL-like dicts) and persist clips + compositions into the database | **Partial** – SML-based DSL-like dicts are stored via `/clips/from-sml`, `/compositions`, `/compositions/from-sml` using `ClipService` and `CompositionService`; full DSL project JSON only reaches `DSLParser.to_database_format` | Add a `dsl_loader.load_dsl_to_db()` that uses `DSLParser.parse_project` + `to_database_format`, then calls `ClipService.create_clip_from_dsl` and `CompositionService.create_composition_from_dsl` |
| `get_dsl_from_db`      | Query specific clips/compositions from DB and reconstruct DSL/spec-compliant structures | **Missing** – only low-level DB dicts exist (`get_clip_with_bars_and_notes`, `get_composition_with_tracks`) | Create a `dsl_exporter.database_to_dsl()` module that reads via services and rebuilds DSL/spec dicts (and optionally full DSL project JSON) |
| `render_dsl_to_midi`   | Turn DSL/spec structures into MIDI data (real-time events and/or `.mid` files) | **Partial** – `MidiClipPlayer` renders a single clip in real-time; `research/midi.py` shows file export patterns, but is not integrated or DSL-aware | Introduce a shared `midi_export` / `ast_to_midi` layer that converts AST/DB dicts into MIDI event streams and `.mid` files, reused by both real-time playback and offline export |
| `play_midi`            | Play MIDI derived from clips/compositions in real time            | **Present (clip-only)** – `MidiClipPlayer.play_dsl_clip` + `services/player/midi_player.play_clip` handle single-clip playback on channel 0 | Fix import paths and treat this as the canonical clip player; later extend with composition-level playback that resolves `CompositionService` + `ClipService` output into multi-track, tempo-aware event streams |

## High-Level Design: Artifacts by Feature

| Feature                | New artifacts (modules / Pydantic models / functions)                                                                                                   | Existing artifacts to update                                                                                         | Artifacts to deprecate / rename                          |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------|
| `natural_language_to_sml` | `src/services/nl_to_sml.py` with Pydantic `NLToSMLRequest` / `NLToSMLResponse` and a LangGraph-backed `async def natural_language_to_sml(request)` | None yet – future integration point once NL → SML is prioritized                                                    | None                                                     |
| `sml_to_dsl`           | Thin converters (e.g. `sml_to_dsl_clip`, `sml_to_dsl_composition`) in `src/dsl/converters.py` wrapping `clip_from_smil_dict` / `composition_from_smil_dict` and returning spec/DSL dicts | FastAPI endpoints in `src/api/app.py` (`/clips/from-sml`, `/compositions/from-sml`) to call the new converters      | None                                                     |
| `store_dsl_to_db`      | `src/services/dsl_loader.py` with Pydantic `DSLLoadConfig` (e.g. source path/JSON) and `async def load_dsl_to_db(config) -> int` orchestrating full DSL project → DB | None strictly required; optional new API endpoint (e.g. `/dsl/load`) could call `load_dsl_to_db`                    | None                                                     |
| `get_dsl_from_db`      | `src/services/dsl_exporter.py` with Pydantic `DSLProjectModel` mirroring `DSL.md` and helpers like `async def composition_to_dsl(composition_id) -> DSLProjectModel` | `ClipService` / `CompositionService` will be used as dependencies but not structurally changed; optional new API endpoints for DSL export | None                                                     |
| `render_dsl_to_midi`   | `src/services/midi_export.py` with `MidiExportOptions` (Pydantic) plus `def dsl_to_midi(dsl_project, output_path, options)` and `async def database_to_midi(composition_id, output_path, options)` sharing AST/DB → MIDI event logic | Factor or reuse scheduling logic from `MidiClipPlayer._schedule_events`; integrate patterns from `research/midi.py` for `.mid` creation | Treat `research/midi.py` as reference-only (no direct use) |
| `play_midi`            | Extended APIs in `src/services/player/midi_player.py`, e.g. Pydantic `PlaybackConfig` and `def play_midi_clip(clip_dict, config)`; later, `async def play_composition(composition_id, config)` using services + `midi_export` | Fix imports to use `MidiClipPlayer` from `src/services/player/midi_builder.py`; optionally extend to handle compositions/multi-track | Deprecate the ad hoc example usage in favor of tested helpers (optional) |

## Current State Analysis

Date: 2025-12-10
Purpose: Document overlapping functionality and plan reorganization

## Executive Summary

### 🔴 Critical Findings:
1. **PRIMARY USE CASE MISSING**: No way to export database composition → MIDI file for DAW
2. **MISLEADING NAMES**: `midi_builder.py` does real-time playback, NOT MIDI file building
3. **LIMITED PLAYBACK**: Only single clips can be played, not full compositions with multiple tracks

### ✅ What Works:
- DSL parsing is clean and well-structured
- Database services properly implemented with async/await
- Real-time clip playback works well
- Good separation: `midi_builder.py` (core engine) + `midi_player.py` (convenience wrapper)

### ❌ What's Missing:
- **Database → MIDI file export** (PRIMARY USE CASE!)
- **Composition playback** (only single clips work, no multi-track)
- **Actual MIDI file builder** (no `.mid` file creation capability)
- Tempo/key map handling during playback
- Channel assignment per track

---

## Feature Requirements

### Primary Use Case
**Database → MIDI File Export for DAW**
- Pull composition from database
- Convert to MIDI file format (`.mid`)
- Load into DAW (Reaper, Logic, etc.)

### Secondary Use Case
**DSL → Live Playback**
- Load clip or composition from DSL JSON
- Convert to MIDI events
- Send to MidiClipPlayer for real-time playback

---

## Current Implementation Inventory

### 1. `src/dsl/dsl_parser.py`
**Purpose:** Parse DSL JSON into AST models

**What it does:**
- Reads DSL JSON structure (see `DSL.md`)
- Parses `clip_library` into `Clip` objects with `ClipBar` and notes
- Parses `tracks` into `Track` objects with `TrackBarRef` references
- Creates `Composition` AST with metadata (tempo, meter, key)
- Groups notes by bar based on `start_beat` (assumes 4 beats/bar)
- Applies `bar_overrides` for expression curves
- Converts to "database-ready format" via `to_database_format()`

**Key methods:**
- `parse_project(dsl_json)` → `Composition` AST
- `to_database_format(composition)` → dict with `{composition, clips, tracks}`

**Input:** DSL JSON
**Output:** Pydantic AST models (`Composition`, `Track`, `Clip`, `ClipBar`)

**Dependencies:**
- `src/dsl/sml_ast.py` (Pydantic models)

**Notes:**
- ✅ Clean separation: parsing only
- ✅ Well-tested (see `test_dsl_parser.py`)
- ⚠️ `to_database_format()` returns dict, not database records
- ⚠️ Doesn't actually INSERT into database

---

### 2. `src/services/player/midi_builder.py`
**Purpose:** Core MIDI event scheduling and playback engine

**What it does:**
- Contains `MidiClipPlayer` class (the core real-time playback engine)
- Schedules MIDI events from clip data structure
- Interpolates expression curves (velocity, CC, pitch bend, aftertouch)
- Sends MIDI messages to either MIDI port or FluidSynth synthesizer
- Handles real-time playback with precise timing

**Key classes:**
- `MidiClipPlayer(midi_port_name, fluidsynth, bpm, beats_per_bar, loop)`
  - `_schedule_events(clip)` → Converts clip bars to timed events
  - `_interpolate_curve(curve, target_time)` → Expression interpolation
  - `_send_message(kind, param1, param2)` → Output to MIDI port or synth
  - `play_dsl_clip(clip)` → Main playback loop

**Input:** Clip dict with `{bars: [{bar_index, notes[], velocity_curve[], cc, ...}]}`
**Output:** Real-time MIDI messages (audio playback)

**Dependencies:**
- `mido` (MIDI protocol)
- `fluidsynth` (optional, for software synth)

**Notes:**
- ✅ Core engine is well-structured
- ✅ Handles complex expression curves with interpolation
- ⚠️ **Misleading name**: "builder" typically means file creation, this does playback
- ⚠️ Only plays single clips (no composition/multi-track support)
- ⚠️ Hardcoded to MIDI channel 0
- ❌ Does NOT create MIDI files (`.mid`) - only real-time playback

---

### 2b. `src/services/player/midi_player.py`
**Purpose:** Convenience wrapper for midi_builder.py with FluidSynth setup

**What it does:**
- Imports `MidiClipPlayer` from `midi_builder.py` (line 5: `from midi_clip_player import`)
- Provides `play_clip()` convenience function that handles full playback setup:
  1. Creates FluidSynth instance
  2. Loads SoundFont (.sf2 file)
  3. Configures audio driver (coreaudio/dsound/alsa)
  4. Instantiates `MidiClipPlayer` with the synth
  5. Plays clip
  6. Cleans up resources
- Includes example usage with sample clip JSON

**Key functions:**
- `play_clip(clip_data, sf2_path=None, bpm=120, loop=False)` - One-line playback

**Input:** Clip dict + optional SoundFont path
**Output:** Audio playback through FluidSynth

**Dependencies:**
- `fluidsynth` (pyFluidSynth library)
- `midi_clip_player.MidiClipPlayer` (should be `midi_builder.MidiClipPlayer`)

**Notes:**
- ✅ Good convenience wrapper pattern
- ✅ Handles resource cleanup properly (try/finally)
- ✅ Includes working example code
- ⚠️ Import statement may be incorrect: `from midi_clip_player import` (file doesn't exist?)
  - Should probably be: `from midi_builder import MidiClipPlayer`
- ⚠️ Hardcoded SoundFont path "FluidR3_GM.sf2"
- ⚠️ Platform-specific driver ("coreaudio" for Mac only)

**Relationship:**
```
midi_player.py (convenience wrapper)
    ↓ imports & injects FluidSynth
midi_builder.py (MidiClipPlayer core engine)
```

---

### 3. `src/services/clip_service.py`
**Purpose:** Business logic for clip database operations

**What it does:**
- **CREATE**: `create_clip_from_dsl(dsl_clip)` - Inserts clip → clip_bars → notes into DB
  - Takes DSL clip format (from parser output)
  - Async/await pattern with sessions
  - Returns clip_id

- **READ**: `get_clip_with_bars_and_notes(clip_id)` - Retrieves full clip hierarchy
  - Returns dict with nested bars and notes

- **SEARCH**: `find_clips_by_tag(tag)`, `find_clips_by_name(pattern)`

- **DELETE**: `delete_clip(clip_id)` - Cascade deletes

**Key methods:**
- `create_clip_from_dsl(dsl_clip)` → `clip_id`
- `get_clip_with_bars_and_notes(clip_id)` → `dict`

**Input:** DSL clip dict (from `dsl_parser.to_database_format()`)
**Output:** Database records OR dict representations

**Dependencies:**
- `src/repository` (ClipRepository, ClipBarRepository, NoteRepository)
- `src/core` (Pydantic models)

**Notes:**
- ✅ Proper service layer pattern
- ✅ Handles database transactions
- ✅ Async implementation
- ⚠️ Takes DSL format but doesn't parse it (expects pre-parsed)
- ⚠️ `get_clip_with_bars_and_notes()` returns format compatible with MidiClipPlayer

---

### 4. `src/services/composition_service.py`
**Purpose:** Business logic for composition database operations

**What it does:**
- **CREATE**: `create_composition_from_dsl(dsl_composition)` - Inserts composition → tracks → track_bars
  - Takes DSL composition format
  - Does NOT create clips (assumes clips already exist)
  - Returns composition_id

- **READ**: `get_composition_with_tracks(composition_id)` - Retrieves full composition
  - Returns dict with nested tracks and track_bars

- **SEARCH**: `find_compositions_by_name()`, `find_compositions_by_tempo()`, `get_track_by_name()`

- **DELETE**: `delete_composition(composition_id)` - Cascade deletes

**Key methods:**
- `create_composition_from_dsl(dsl_composition)` → `composition_id`
- `get_composition_with_tracks(composition_id)` → `dict`

**Input:** DSL composition dict
**Output:** Database records OR dict

**Dependencies:**
- `src/repository` (CompositionRepository, TrackRepository, TrackBarRepository)
- `src/core` (Pydantic models)

**Notes:**
- ✅ Proper service layer pattern
- ✅ Async implementation
- ⚠️ Requires clips to already exist in DB
- ⚠️ Doesn't handle full DSL → DB pipeline (need to create clips first)

---

### 5. `src/services/player/midi_player.py`
**Purpose:** Real-time MIDI playback using FluidSynth

**What it does:**
- **PLAYBACK**: `play_dsl_clip(clip)` - Plays clip in real-time
  - Takes clip dict (database format)
  - Schedules MIDI events based on timing
  - Interpolates expression curves (velocity, CC, pitch bend, aftertouch)
  - Supports looping
  - Can output to MIDI port OR FluidSynth

- **Helper**: `play_clip(clip_data, sf2_path, bpm, loop)` - Convenience wrapper

**Key classes:**
- `MidiClipPlayer` - Main player class

**Input:** Clip dict with structure:
```python
{
  "bars": [
    {
      "bar_index": int,
      "notes": [{"pitch": int, "start_beat": float, "duration_beats": float, ...}],
      "velocity_curve": [...],
      "cc": {...},
      "pitch_bend_curve": [...],
      "aftertouch_curve": [...],
      "pedal_events": [...]
    }
  ]
}
```

**Output:** Real-time MIDI playback (audio)

**Dependencies:**
- `mido` (MIDI messages)
- `fluidsynth` (software synthesizer)

**Notes:**
- ✅ Works with output from `clip_service.get_clip_with_bars_and_notes()`
- ✅ Handles real-time expression interpolation
- ✅ Supports both MIDI ports and software synth
- ⚠️ Only plays single clips, not full compositions
- ⚠️ Hardcoded to channel 0
- ⚠️ No composition/multi-track support

---

### 6. `research/midi.py`
**Purpose:** Research/example code for MIDI file generation

**What it does:**
- Example template using `mido` + `music21`
- Creates MIDI **files** (not real-time playback)
- Music theory helpers (scales, chords, intervals)
- Algorithmic composition examples

**Key functions:**
- `create_midi_file()` - Creates `.mid` file structure
- `add_note_to_track()` - Adds notes to tracks
- `get_scale_notes()`, `get_chord_notes()` - Music theory
- Example compositions

**Input:** Programmatic note data
**Output:** MIDI files (`.mid`)

**Dependencies:**
- `mido`
- `music21`

**Notes:**
- ⚠️ Research code, not production
- ⚠️ No integration with DSL or database
- ✅ Good reference for MIDI file creation
- ✅ Shows how to handle multi-track MIDI files

---

## Gap Analysis

### ✅ What We HAVE:

1. **DSL → AST parsing** (`dsl_parser.py`)
2. **DSL → Database** (`clip_service.py`, `composition_service.py`)
3. **Database → Real-time playback** (single clip via `midi_player.py`)
4. **Research MIDI file creation** (`research/midi.py`)

### ❌ What We're MISSING:

1. **Database → MIDI File** (primary use case!)
   - No way to export composition from DB to `.mid` file
   - Can't load into DAW

2. **DSL → MIDI File** (direct path)
   - Currently need to go: DSL → DB → (missing) → MIDI file

3. **Composition playback**
   - `midi_player.py` only handles single clips
   - No multi-track playback
   - No composition-level tempo/key changes

4. **`midi_builder.py`**
   - File referenced but doesn't exist

---

## Overlap & Redundancy Analysis

### Overlap 1: DSL Format Handling
**Who handles it:**
- `dsl_parser.py` - Parses DSL JSON
- `clip_service.py` - Expects DSL format from parser
- `composition_service.py` - Expects DSL format

**Redundancy:**
- ✅ Good separation: parser converts, services consume
- ⚠️ Services expect "database-ready dict" not raw DSL

### Overlap 2: Database Format → Playback Format
**Who handles it:**
- `clip_service.get_clip_with_bars_and_notes()` - Returns dict
- `midi_player.play_dsl_clip()` - Expects dict

**Redundancy:**
- ✅ These formats are compatible!
- ⚠️ Format is undocumented (implicit contract)

### Overlap 3: MIDI Event Generation
**Who handles it:**
- `midi_player.py` - Real-time MIDI events (messages)
- `research/midi.py` - MIDI file creation (tracks + messages)

**Redundancy:**
- ⚠️ Different paradigms (real-time vs file)
- ⚠️ No shared code
- ⚠️ Would need to duplicate for composition export

---

## Recommended Architecture

Based on analysis, here's the proposed clean architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                        INPUT LAYER                           │
├─────────────────────────────────────────────────────────────┤
│  DSL JSON File                      Database Query           │
│        │                                   │                 │
│        v                                   v                 │
│  dsl_parser.py                    Repository Layer           │
│        │                                   │                 │
│        v                                   v                 │
│  Pydantic AST Models            Pydantic Models              │
└────────┬────────────────────────────────────┬───────────────┘
         │                                    │
         v                                    v
┌─────────────────────────────────────────────────────────────┐
│                     CONVERSION LAYER                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ast_to_midi.py                    database_to_midi.py      │
│  - Takes AST models                - Takes DB dicts          │
│  - Builds MIDI structure           - Loads full composition  │
│  - Handles expressions             - Converts to AST         │
│  - Multi-track support             - Delegates to ast_to_midi│
│                                                              │
└────────┬────────────────────────────────────┬───────────────┘
         │                                    │
         v                                    v
┌─────────────────────────────────────────────────────────────┐
│                      OUTPUT LAYER                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  midi_file_builder.py            midi_player.py             │
│  - Creates .mid files            - Real-time playback        │
│  - For DAW export                - Live performance          │
│  - Uses mido                     - Uses mido + FluidSynth    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Proposed Module Functions

#### 1. `load_dsl_to_db(dsl_file_path)` → `composition_id`
**Location:** New module `src/services/dsl_loader.py`
```python
async def load_dsl_to_db(dsl_file_path: str) -> int:
    """
    Load complete DSL project into database.

    Steps:
    1. Parse DSL file
    2. Create clips in database
    3. Create composition with tracks
    4. Return composition_id
    """
```

**Uses:**
- `dsl_parser.parse_dsl_file()`
- `clip_service.create_clip_from_dsl()`
- `composition_service.create_composition_from_dsl()`

---

#### 2. `database_to_dsl(composition_id)` → `dsl_dict`
**Location:** New module `src/services/dsl_exporter.py`
```python
async def database_to_dsl(composition_id: int) -> dict:
    """
    Export database composition back to DSL format.

    Steps:
    1. Load composition with tracks
    2. Load all referenced clips
    3. Reconstruct DSL structure
    4. Return DSL-compliant dict
    """
```

**Uses:**
- `composition_service.get_composition_with_tracks()`
- `clip_service.get_clip_with_bars_and_notes()`

---

#### 3. `dsl_to_midi(dsl_dict, output_path)` → `.mid` file
**Location:** New module `src/services/midi_export.py`
```python
def dsl_to_midi(dsl_dict: dict, output_path: str,
                include_all_tracks: bool = True) -> None:
    """
    Convert DSL to MIDI file.

    Steps:
    1. Parse DSL if needed
    2. Convert AST to MIDI structure
    3. Handle multi-track
    4. Apply tempo/key changes
    5. Write .mid file
    """
```

**Uses:**
- `dsl_parser.parse_project()` (if raw DSL)
- New: `ast_to_midi_file()` function

---

#### 4. `database_to_midi(composition_id, output_path)` → `.mid` file
**Location:** `src/services/midi_export.py`
```python
async def database_to_midi(composition_id: int, output_path: str) -> None:
    """
    Export database composition to MIDI file (PRIMARY USE CASE).

    Steps:
    1. Load composition from DB
    2. Convert to DSL format
    3. Convert DSL to MIDI
    4. Write file
    """
```

**Uses:**
- `database_to_dsl()`
- `dsl_to_midi()`

---

#### 5. `play_midi(clip_or_composition_dict, ...)` → audio
**Location:** Enhanced `src/services/player/midi_player.py`
```python
def play_midi(data: dict,
              mode: str = 'clip',  # 'clip' or 'composition'
              sf2_path: str = None,
              bpm: int = 120,
              loop: bool = False) -> None:
    """
    Play clip or composition in real-time.

    Modes:
    - 'clip': Single clip playback (current functionality)
    - 'composition': Multi-track playback with tempo changes
    """
```

**Enhances:** Current `MidiClipPlayer`

---

## Implementation Priority

### Phase 1: Close the Gap (High Priority)
1. ✅ Create `src/services/midi_export.py`
   - `database_to_midi()` - PRIMARY USE CASE
   - `dsl_to_midi()`
   - Core conversion logic

2. ✅ Create `src/services/dsl_loader.py`
   - `load_dsl_to_db()` - Complete DSL → DB pipeline

### Phase 2: Round-trip Support (Medium Priority)
3. ✅ Create `src/services/dsl_exporter.py`
   - `database_to_dsl()` - Allow DB → DSL round-trip

### Phase 3: Enhanced Playback (Lower Priority)
4. ✅ Enhance `midi_player.py`
   - Add composition playback
   - Multi-track support
   - Tempo map handling

---

## Code Quality Assessment

### Good Patterns ✅
- Clean separation: parser, services, repositories
- Async/await for database operations
- Pydantic models for validation
- Service layer abstracts DB operations

### Issues to Address ⚠️
- Missing `midi_builder.py` (referenced but doesn't exist)
- No MIDI file export capability (PRIMARY USE CASE!)
- Implicit format contracts between modules
- Limited documentation of data formats
- `midi_player.py` only handles clips, not compositions

### Technical Debt 🔧
- `research/midi.py` has useful MIDI file code that should be integrated
- Expression curve handling in player should be shared with file export
- Need unified MIDI structure format
- Need format documentation between modules

---

## Next Steps

1. **Immediate:** Create `midi_export.py` with `database_to_midi()` function
2. **Document:** Create format specs for module interfaces
3. **Consolidate:** Integrate useful code from `research/midi.py`
4. **Test:** Write tests for new export functionality
5. **Enhance:** Add composition playback to `midi_player.py`

---

## Questions to Resolve

1. ❓ What happened to `midi_builder.py`? Should we create it?
2. ❓ Should we keep `research/midi.py` or integrate its functionality?
3. ❓ Do we need bi-directional DSL ↔ DB conversion?
4. ❓ Should MIDI export support partial compositions (single track)?
5. ❓ What format should `get_clip_with_bars_and_notes()` return?

---

## Appendix: Data Format Flows

### Current Flow (Incomplete)
```
DSL JSON
  ↓ [dsl_parser]
AST Models (Pydantic)
  ↓ [dsl_parser.to_database_format()]
Dict {composition, clips, tracks}
  ↓ [clip_service.create_clip_from_dsl()]
Database Records
  ↓ [clip_service.get_clip_with_bars_and_notes()]
Dict (for playback)
  ↓ [midi_player.play_dsl_clip()]
Audio ✅

[DATABASE → MIDI FILE: MISSING! ❌]
```

### Proposed Complete Flow
```
DSL JSON → [parser] → AST → [to_db] → Database
                      ↓                    ↓
                   [to_midi] ←-----[from_db]
                      ↓
                  MIDI File ✅

DSL/DB → [player] → Audio ✅
```
