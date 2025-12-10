# OSC DSL (Domain-Specific Language) Documentation

## Overview

The OSC DSL is a JSON-based language for defining musical compositions. It provides a simple, human-readable format for creating songs with multiple tracks, clips, and expressive controls. The DSL parser converts this format into a database-ready structure for MIDI playback.

## Architecture

```
DSL JSON → DSL Parser → AST Models → Database Format → MIDI Player
```

- **DSL JSON**: Human-written song definition (this format)
- **DSL Parser** (`dsl_parser.py`): Converts JSON to AST
- **AST Models** (`sml_ast.py`): Pydantic models representing the song structure
- **Database Format**: Normalized data ready for storage
- **MIDI Player**: Converts to MIDI events for playback

## Quick Start

### Minimal Example

Here's the simplest possible song - a single note:

```json
{
  "project": {
    "name": "hello_world",
    "ticks_per_quarter": 480,
    "tempo_map": [{"bar": 1, "tempo_bpm": 120}],
    "meter_map": [{"bar": 1, "numerator": 4, "denominator": 4}],
    "key_map": [{"bar": 1, "key": "C", "mode": "major"}],
    "tracks": {
      "melody": {
        "instrument": {"name": "piano", "midi_channel": 0},
        "clips": [
          {"clip_instance_id": "m1", "clip_id": 1, "start_bar": 1, "length_bars": 1}
        ]
      }
    },
    "clip_library": [
      {
        "clip_id": 1,
        "name": "middle-c",
        "notes": [
          {"pitch": 60, "start_beat": 0.0, "duration_beats": 4.0}
        ]
      }
    ]
  }
}
```

This plays middle C (MIDI note 60) for 4 beats at 120 BPM.

### Usage

```python
from src.dsl.dsl_parser import parse_dsl_file

# Parse DSL file
composition = parse_dsl_file("my_song.json")

# Convert to database format
parser = DSLParser()
composition = parser.parse_project(dsl_json)
db_data = parser.to_database_format(composition)
```

## Complete Field Reference

### Project Structure

```
{
  "project": {
    "name": "string",              // Project name
    "ticks_per_quarter": 480,      // MIDI resolution (typically 480)
    "tempo_map": [...],             // Tempo changes
    "meter_map": [...],             // Time signature changes
    "key_map": [...],               // Key signature changes
    "tracks": {...},                // Named tracks
    "loops": [...],                 // Loop regions (optional)
    "clip_library": [...]           // Reusable clips
  }
}
```

### Tempo Map

Defines tempo changes throughout the song.

```json
"tempo_map": [
  {"bar": 1, "tempo_bpm": 120},    // Start at 120 BPM
  {"bar": 9, "tempo_bpm": 140}     // Speed up to 140 BPM at bar 9
]
```

- **bar** (integer): Bar number where tempo changes (1-based)
- **tempo_bpm** (integer): Tempo in beats per minute (typical range: 60-200)

### Meter Map

Defines time signature changes.

```json
"meter_map": [
  {"bar": 1, "numerator": 4, "denominator": 4},    // 4/4 time
  {"bar": 5, "numerator": 3, "denominator": 4}     // Switch to 3/4 at bar 5
]
```

- **bar** (integer): Bar number where meter changes
- **numerator** (integer): Beats per bar (top number)
- **denominator** (integer): Beat unit (bottom number, typically 4)

### Key Map

Defines key signature changes.

```json
"key_map": [
  {"bar": 1, "key": "C", "mode": "major"},
  {"bar": 9, "key": "Am", "mode": "minor"}
]
```

- **bar** (integer): Bar number where key changes
- **key** (string): Root note (A-G with optional # or b)
- **mode** (string): "major" or "minor"

### Tracks

Tracks organize clips into parallel musical lines.

```json
"tracks": {
  "lead": {                        // Track name (any string)
    "instrument": {
      "name": "lead-synth",        // Instrument name (for reference)
      "midi_channel": 0            // MIDI channel (0-15)
    },
    "clips": [...]                 // Clip instances
  }
}
```

### Clip Instances

References to clips in the library, placed at specific bars.

```json
{
  "clip_instance_id": "lead_intro",  // Unique ID for this instance
  "clip_id": 8,                      // References clip in clip_library
  "start_bar": 1,                    // Bar where clip starts (1-based)
  "length_bars": 2,                  // Number of bars to play
  "bar_overrides": [...]             // Optional expression overrides
}
```

- **clip_instance_id** (string): Unique identifier for tracking
- **clip_id** (integer): ID of clip in clip_library
- **start_bar** (integer): Starting bar position (1-based)
- **length_bars** (integer): How many bars to play from the clip
- **bar_overrides** (array, optional): Bar-level expression curves

### Clip Library

Reusable musical patterns (clips) containing notes.

```json
{
  "clip_id": 8,                    // Unique ID
  "name": "lead-riff-intro",       // Descriptive name
  "style": "latin",                // Optional style tag
  "notes": [                       // Array of notes/rests
    {
      "pitch": 60,                 // MIDI note number (0-127)
      "start_beat": 0.0,           // Beat position (0.0 = bar start)
      "duration_beats": 1.0        // Length in beats
    },
    {
      "is_rest": true,             // Rest (no pitch)
      "start_beat": 3.0,
      "duration_beats": 1.0
    }
  ]
}
```

**Note Fields:**
- **pitch** (integer): MIDI note number (60 = middle C, range 0-127)
- **start_beat** (float): Position in beats from start of clip (0.0 = first beat)
- **duration_beats** (float): Length in beats (1.0 = quarter note in 4/4)
- **is_rest** (boolean, optional): True for rests (no pitch played)

**MIDI Note Reference:**
- C4 (middle C) = 60
- A4 (440 Hz) = 69
- Each semitone = +/- 1
- Each octave = +/- 12

### Bar Overrides

Add expression curves to specific bars within a clip instance.

```json
"bar_overrides": [
  {
    "bar_index": 0,                // Clip-relative bar index (0-based)
    "velocity_curve": [            // Dynamic curve
      {"time": 0, "value": 70},
      {"time": 4, "value": 110}
    ],
    "cc_lanes": {                  // MIDI CC controllers
      "1": [{"time": 0, "value": 64}],    // Mod wheel
      "11": [{"time": 0, "value": 100}]   // Expression
    },
    "pitch_bend_curve": [          // Pitch bend
      {"time": 0, "value": 0},
      {"time": 4, "value": 200}
    ],
    "aftertouch_curve": null,      // Channel aftertouch (optional)
    "pedal_events": null,          // Sustain pedal (optional)
    "metadata": {"tag": "intro"}   // Custom metadata
  }
]
```

- **bar_index** (integer): Which bar in the clip (0-based, relative to clip start)
- **velocity_curve** (array): Dynamic changes over time
- **cc_lanes** (object): MIDI CC changes (key = CC number, value = events)
- **pitch_bend_curve** (array): Pitch bend events
- **time** (float): Position in beats within the bar
- **value** (float): MIDI value (typically 0-127)

**Common CC Numbers:**
- 1: Modulation wheel
- 7: Volume
- 10: Pan
- 11: Expression
- 64: Sustain pedal

### Loops

Define repeating sections (optional).

```json
"loops": [
  {
    "start_bar": 5,        // Loop start bar
    "length_bars": 4,      // Loop length
    "repeat_count": 2      // How many times to repeat
  }
]
```

## Step-by-Step Tutorial

### Step 1: Create a Clip

Start by defining a musical pattern in the clip_library:

```json
"clip_library": [
  {
    "clip_id": 1,
    "name": "simple-melody",
    "notes": [
      {"pitch": 60, "start_beat": 0.0, "duration_beats": 1.0},  // C
      {"pitch": 62, "start_beat": 1.0, "duration_beats": 1.0},  // D
      {"pitch": 64, "start_beat": 2.0, "duration_beats": 1.0},  // E
      {"pitch": 65, "start_beat": 3.0, "duration_beats": 1.0}   // F
    ]
  }
]
```

### Step 2: Add a Track

Create a track and reference your clip:

```json
"tracks": {
  "melody": {
    "instrument": {"name": "piano", "midi_channel": 0},
    "clips": [
      {
        "clip_instance_id": "melody_1",
        "clip_id": 1,
        "start_bar": 1,
        "length_bars": 1
      }
    ]
  }
}
```

### Step 3: Set Project Metadata

Add tempo, meter, and key:

```json
"tempo_map": [{"bar": 1, "tempo_bpm": 120}],
"meter_map": [{"bar": 1, "numerator": 4, "denominator": 4}],
"key_map": [{"bar": 1, "key": "C", "mode": "major"}]
```

### Step 4: Add Multiple Tracks

Create a bass line:

```json
"clip_library": [
  // ... previous clips ...
  {
    "clip_id": 2,
    "name": "bass-line",
    "notes": [
      {"pitch": 36, "start_beat": 0.0, "duration_beats": 2.0},  // C1
      {"pitch": 38, "start_beat": 2.0, "duration_beats": 2.0}   // D1
    ]
  }
],
"tracks": {
  "melody": { /* ... */ },
  "bass": {
    "instrument": {"name": "bass", "midi_channel": 1},
    "clips": [
      {"clip_instance_id": "bass_1", "clip_id": 2, "start_bar": 1, "length_bars": 1}
    ]
  }
}
```

### Step 5: Add Expression

Add dynamics to a bar:

```json
{
  "clip_instance_id": "melody_1",
  "clip_id": 1,
  "start_bar": 1,
  "length_bars": 1,
  "bar_overrides": [
    {
      "bar_index": 0,
      "velocity_curve": [
        {"time": 0, "value": 80},   // Start soft
        {"time": 4, "value": 110}   // Crescendo
      ]
    }
  ]
}
```

## Common Patterns

### Repeating a Clip

Play the same clip multiple times:

```json
"clips": [
  {"clip_instance_id": "verse_1", "clip_id": 10, "start_bar": 1, "length_bars": 4},
  {"clip_instance_id": "verse_2", "clip_id": 10, "start_bar": 5, "length_bars": 4},
  {"clip_instance_id": "verse_3", "clip_id": 10, "start_bar": 9, "length_bars": 4}
]
```

### Different Clips in Sequence

```json
"clips": [
  {"clip_instance_id": "intro", "clip_id": 1, "start_bar": 1, "length_bars": 4},
  {"clip_instance_id": "verse", "clip_id": 2, "start_bar": 5, "length_bars": 8},
  {"clip_instance_id": "chorus", "clip_id": 3, "start_bar": 13, "length_bars": 8}
]
```

### Multi-bar Clips

A clip can span multiple bars:

```json
{
  "clip_id": 5,
  "name": "long-phrase",
  "notes": [
    // Bar 1
    {"pitch": 60, "start_beat": 0.0, "duration_beats": 4.0},
    // Bar 2 (starts at beat 4.0)
    {"pitch": 62, "start_beat": 4.0, "duration_beats": 4.0}
  ]
}
```

The parser automatically groups notes into bars based on `start_beat` (assumes 4 beats per bar in 4/4 time).

## Troubleshooting

### "Clip X not found in clip_library"
- Ensure `clip_id` in tracks matches an entry in `clip_library`
- Check for typos in clip IDs

### "Bar overflow: total units > units_per_bar"
- Notes exceed bar length
- Check that `start_beat + duration_beats` doesn't exceed bar boundaries
- In 4/4 time, beats should stay within 0.0-4.0 per bar

### "project key not found"
- DSL must have top-level `"project"` key
- Check JSON syntax for missing braces or commas

### Notes not playing
- Verify MIDI channel numbers are correct (0-15)
- Check that `start_bar` positions don't overlap unexpectedly
- Ensure `length_bars` doesn't exceed available clip bars

## Advanced Topics

### Custom Time Signatures

Use 3/4 waltz time:

```json
"meter_map": [{"bar": 1, "numerator": 3, "denominator": 4}]
```

Notes in 3/4 have 3 beats per bar instead of 4.

### Tempo Changes

Accelerando effect:

```json
"tempo_map": [
  {"bar": 1, "tempo_bpm": 100},
  {"bar": 5, "tempo_bpm": 120},
  {"bar": 9, "tempo_bpm": 140}
]
```

### Complex CC Automation

Multiple CC lanes for filter sweeps:

```json
"cc_lanes": {
  "74": [  // Filter cutoff
    {"time": 0.0, "value": 20},
    {"time": 2.0, "value": 100},
    {"time": 4.0, "value": 20}
  ],
  "71": [  // Filter resonance
    {"time": 0.0, "value": 64},
    {"time": 2.0, "value": 100}
  ]
}
```

## File Organization

Recommended structure:

```
my_project/
  songs/
    song_1.json          # Complete DSL file
    song_2.json
  clips/
    drums.json           # Reusable clip libraries
    bass.json
    melody.json
```

You can split large projects into multiple files and combine them programmatically.

## Examples

See the `examples/` directory for complete, runnable examples:

- `01-simple-melody.json` - Single track basics
- `02-multi-track.json` - Multiple tracks with timing
- `03-expressions.json` - Expression curves and CC
- `04-complete-song.json` - Full song structure

## Further Reading

- [GLOSSARY.md](GLOSSARY.md) - Detailed term definitions
- [DSL.md](DSL.md) - Original DSL specification
- `sml_ast.py` - AST model documentation
- `dsl_parser.py` - Parser implementation
