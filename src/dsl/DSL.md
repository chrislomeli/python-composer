
# OSC DSL Specification

> **For comprehensive documentation, see [README.md](README.md) and [GLOSSARY.md](GLOSSARY.md)**

## Complete Example

This example demonstrates all major features of the DSL:
- Multiple tracks (lead and bass)
- Clip library with reusable patterns
- Bar-level expression overrides
- Tempo, meter, and key maps
- Loop regions

```json
{
  "project": {
    // === PROJECT METADATA ===
    "name": "phrase_loop_example",          // Project name
    "ticks_per_quarter": 480,               // MIDI resolution (standard)

    // === TEMPO, METER, AND KEY ===
    "tempo_map": [
      { "bar": 1, "tempo_bpm": 120 }        // 120 BPM starting at bar 1
    ],
    "meter_map": [
      { "bar": 1, "numerator": 4, "denominator": 4 }  // 4/4 time
    ],
    "key_map": [
      { "bar": 1, "key": "C", "mode": "major" }       // C major
    ],

    // === TRACKS ===
    // Tracks are parallel musical lines, each with an instrument
    "tracks": {

      // --- Lead Track ---
      "lead": {
        "instrument": {
          "name": "lead-kazoo",             // Instrument name (for reference)
          "midi_channel": 0                 // MIDI channel 0
        },
        "clips": [
          {
            "clip_instance_id": "lead_1",   // Unique ID for this instance
            "clip_id": 8,                   // References clip 8 in clip_library
            "start_bar": 1,                 // Starts at bar 1
            "length_bars": 2,               // Play 2 bars of the clip

            // Bar-level expression overrides
            "bar_overrides": [
              {
                "bar_index": 1,             // Override clip's bar 1 (0-based)

                // Velocity curve (dynamics over time)
                "velocity_curve": [
                  { "time": 0, "value": 90 },    // Start at velocity 90
                  { "time": 4, "value": 100 }    // End at velocity 100 (crescendo)
                ],

                // MIDI CC automation
                "cc_lanes": {
                  "1": [                         // CC 1 = Modulation wheel
                    { "time": 0, "value": 64 }
                  ]
                },

                // Pitch bend curve
                "pitch_bend_curve": [
                  { "time": 0, "value": 0 },     // Start at center
                  { "time": 4, "value": 200 }    // Bend up 2 semitones
                ],

                "aftertouch_curve": null,
                "pedal_events": null,
                "metadata": {
                  "tag": "intro"                 // Custom metadata
                }
              }
            ]
          }
        ]
      },

      // --- Bass Track ---
      "bass": {
        "instrument": {
          "name": "bass-kazoo",
          "midi_channel": 1                 // MIDI channel 1
        },
        "clips": [
          {
            "clip_instance_id": "bass_1",
            "clip_id": 10,                  // References clip 10
            "start_bar": 1,
            "length_bars": 2
            // No bar_overrides - use default clip expression
          }
        ]
      }
    },

    // === LOOPS ===
    // Define repeating sections
    "loops": [
      {
        "start_bar": 5,                     // Loop starts at bar 5
        "length_bars": 4,                   // Loop is 4 bars long (bars 5-8)
        "repeat_count": 1                   // Play loop 1 additional time (2x total)
      }
    ],

    // === CLIP LIBRARY ===
    // Reusable musical patterns
    "clip_library": [
      {
        "clip_id": 8,                       // Unique clip ID
        "name": "lead-riff-intro",          // Descriptive name
        "style": "latin",                   // Optional style tag

        // Notes in the clip
        "notes": [
          // Note format: pitch (MIDI number), start_beat (position), duration_beats (length)
          { "pitch": 60, "start_beat": 0.0,  "duration_beats": 1.0 },  // C4, beat 0, quarter note
          { "pitch": 64, "start_beat": 1.0,  "duration_beats": 1.0 },  // E4, beat 1, quarter note
          { "pitch": 67, "start_beat": 2.0,  "duration_beats": 1.0 },  // G4, beat 2, quarter note
          { "is_rest": true, "start_beat": 3.0, "duration_beats": 1.0 } // Rest, beat 3, quarter note
        ]
      },
      {
        "clip_id": 9,
        "name": "lead-riff-bridge",
        "style": "latin",
        "notes": [
          { "pitch": 60, "start_beat": 0.0,  "duration_beats": 1.0 },  // Repeated C4
          { "pitch": 60, "start_beat": 1.0,  "duration_beats": 1.0 },
          { "pitch": 60, "start_beat": 2.0,  "duration_beats": 1.0 },
          { "is_rest": true, "start_beat": 3.0, "duration_beats": 1.0 }
        ]
      },
      {
        "clip_id": 10,
        "name": "bas-riff",
        "style": "latin",
        "notes": [
          { "pitch": 48, "start_beat": 0.0, "duration_beats": 1.0 },   // C2
          { "pitch": 46, "start_beat": 1.0, "duration_beats": 1.0 },   // A#1
          { "pitch": 72, "start_beat": 2.0, "duration_beats": 1.0 },   // C5 (typo? octave jump)
          { "is_rest": true, "start_beat": 3.0, "duration_beats": 1.0 }
        ]
      }
    ]
  }
}

```



# Design Overview

## Core Data Structures

### Project
The top-level container for a complete musical composition.

```
Project {
  name: string
  ticks_per_quarter: integer         // MIDI resolution (typically 480)
  tempo_map: TempoChange[]           // List of tempo changes
  meter_map: MeterChange[]           // List of time signature changes
  key_map: KeyChange[]               // List of key changes
  tracks: {[name: string]: Track}    // Named tracks (key = track name)
  loops: Loop[]                      // Optional loop regions
  clip_library: Clip[]               // Reusable musical patterns
}
```

### Track
A parallel musical line assigned to a specific instrument.

```
Track {
  instrument: {
    name: string                     // Instrument name (for reference)
    midi_channel: integer            // MIDI channel (0-15)
    expression_profile: string       // Optional expression profile name
  }
  clips: ClipInstance[]              // Clip instances placed in this track
}
```

### ClipInstance
A reference to a clip in the library, placed at a specific position.

```
ClipInstance {
  clip_instance_id: string           // Unique identifier for tracking
  clip_id: integer                   // ID of clip in clip_library
  start_bar: integer                 // Bar position in composition (1-based)
  length_bars: integer               // How many bars to play from the clip
  bar_overrides: BarOverride[]       // Optional expression overrides per bar
}
```

### Clip
A reusable musical pattern containing notes and rests.

```
Clip {
  clip_id: integer                   // Unique clip identifier
  name: string                       // Descriptive name
  style: string                      // Optional style tag (e.g., "latin", "jazz")
  notes: NoteEvent[]                 // Array of notes and rests
}
```

### NoteEvent
A single note or rest with timing and expression.

```
NoteEvent {
  // Core properties
  pitch: integer                     // MIDI note number (0-127, omit for rests)
  start_beat: float                  // Position in beats from clip start
  duration_beats: float              // Length in beats
  is_rest: boolean                   // True for rests (no pitch)

  // Performance properties
  velocity: integer                  // Dynamics (0-127, default 90)
  articulation: string               // "normal", "staccato", "legato", "marcato", etc.

  // Expression (optional)
  expression: {
    vibrato_depth: float             // Vibrato intensity (0.0-1.0)
    vibrato_rate: float              // Vibrato speed in Hz
    cents_offset: float              // Pitch adjustment in cents (+/- 100)
  }

  // Semantic metadata (optional)
  semantics: {
    scale_degree: integer            // Position in scale (1=root, 2=2nd, etc.)
    interval_from_prev: integer      // Semitones from previous note
  }
}
```

### BarOverride
Expression curves applied to a specific bar in a clip instance.

```
BarOverride {
  bar_index: integer                 // Bar index within the clip (0-based)
  velocity_curve: CurvePoint[]       // Dynamics curve
  cc_lanes: {[cc: string]: CurvePoint[]}  // MIDI CC automation
  pitch_bend_curve: CurvePoint[]     // Pitch bend curve
  aftertouch_curve: CurvePoint[]     // Channel pressure
  pedal_events: PedalEvent[]         // Sustain pedal events
  metadata: object                   // Custom metadata
}
```

### Supporting Types

```
TempoChange {
  bar: integer                       // Bar number (1-based)
  tempo_bpm: integer                 // Tempo in beats per minute
}

MeterChange {
  bar: integer                       // Bar number (1-based)
  numerator: integer                 // Beats per bar
  denominator: integer               // Beat unit (typically 4)
}

KeyChange {
  bar: integer                       // Bar number (1-based)
  key: string                        // Root note (e.g., "C", "F#", "Bb")
  mode: string                       // "major" or "minor"
}

Loop {
  start_bar: integer                 // Loop start bar (1-based)
  length_bars: integer               // Loop length in bars
  repeat_count: integer              // Number of additional repeats
}

CurvePoint {
  time: float                        // Position in beats
  value: float                       // Value (typically 0-127 for MIDI)
}

PedalEvent {
  time: float                        // Position in beats
  on: boolean                        // True = pedal down, false = pedal up
}
```


---

# Appendix: Legacy Formats

> **Note:** The formats below are from earlier versions and are kept for reference. Use the current format shown above for new projects.

## Legacy Clip Format

### Create three clips (old format)
```aiignore
[
  {
    "name": "lead-riff-intro",
    "style": "latin",
    "instrument": "lead-kazoo",
    "tempo_bpm": 120,
    "voice_bars": [
      {
        "bar_number": 1,
        "notes": [
          {"start_unit":0, "duration_units":8, "pitch_name":"C", "octave":4},
          {"start_unit":8, "duration_units":8, "pitch_name":"E", "octave":4},
          {"start_unit":16, "duration_units":8, "pitch_name":"G", "octave":3},
          {"start_unit":24, "duration_units":8, "is_rest":true}
        ]
      },
      {
        "bar_number": 2,
        "notes": [
          {"start_unit":0, "duration_units":8, "pitch_name":"D", "octave":4},
          {"start_unit":8, "duration_units":4, "pitch_name":"F", "octave":4},
          {"start_unit":16, "duration_units":4, "pitch_name":"A", "octave":3},
          {"start_unit":24, "duration_units":16, "is_rest":true}
        ]
      }
    ]
  },
  {
    "name": "lead-riff-bridge",
    "style": "latin",
    "instrument": "lead-kazoo",
    "tempo_bpm": 120,
    "voice_bars": [
      {
        "bar_number": 1,
        "notes": [
          {"start_unit":0, "duration_units":8, "pitch_name":"C", "octave":4},
          {"start_unit":8, "duration_units":8, "pitch_name":"C", "octave":4},
          {"start_unit":16, "duration_units":8, "pitch_name":"C", "octave":4},
          {"start_unit":24, "duration_units":8, "is_rest":true}
        ]
      },
      {
        "bar_number": 2,
        "notes": [
          {"start_unit":0, "duration_units":8, "pitch_name":"C", "octave":3},
          {"start_unit":8, "duration_units":4, "pitch_name":"C", "octave":3},
          {"start_unit":16, "duration_units":4, "pitch_name":"C", "octave":3},
          {"start_unit":24, "duration_units":16, "is_rest":true}
        ]
      }
    ]
  },
    {
    "name": "bas-riff",
    "style": "latin",
    "instrument": "bass-kazoo",
    "tempo_bpm": 120,
    "voice_bars": [
      {
        "bar_number": 1,
        "notes": [
          {"start_unit":0, "duration_units":8, "pitch_name":"C", "octave":3},
          {"start_unit":8, "duration_units":8, "pitch_name":"A#", "octave":2},
          {"start_unit":16, "duration_units":8, "pitch_name":"C", "octave":4},
          {"start_unit":24, "duration_units":8, "is_rest":true}
        ]
      },
      {
        "bar_number": 2,
        "notes": [
          {"start_unit":0, "duration_units":8, "pitch_name":"C", "octave":3},
          {"start_unit":8, "duration_units":4, "is_rest":true},
          {"start_unit":16, "duration_units":4, "pitch_name":"C", "octave":3},
          {"start_unit":24, "duration_units":16, "is_rest":true}
        ]
      }
    ]
  }
]
```

### Compose clips
```aiignore
{
  "name": "phrase_loop_example",
  "ticks_per_quarter": 480,
  "tempo_bpm": 120,
  "tracks": {
    "lead": [
      {
        "clip_id": 8,
        "start_bar": 1,
        "length_in_bars": 2,
        "clip_bars": [
          {
            "bar_index": 1,
            "velocity_curve": [
              {"time": 0, "value": 90},
              {"time": 4, "value": 100}
            ],
            "cc": {
              "1": [{"time": 0, "value": 64}]
            },
            "pitch_bend_curve": [
              {"time": 0, "value": 0},
              {"time": 4, "value": 200}
            ],
            "aftertouch_curve": null,
            "pedal_events": null,
            "metadata": {"tag": "intro"}
          }
        ]
      }
    ],
    "bass": [
      {"clip_id": 10, "start_bar": 1, "length_in_bars": 2}
    ]
  },
  "loops": [
    {"start_bar": 5, "length_in_bars": 4, "repeat_count": 1}
  ]
}

```



