# OSC DSL Glossary

## Musical Terms

### Bar (Measure)
A segment of time in music defined by a time signature. In 4/4 time, a bar contains 4 quarter-note beats. Bars are numbered starting from 1.

**Example:** Bar 1 contains beats 0.0-4.0, Bar 2 contains beats 4.0-8.0

### Beat
The basic unit of time in music. In 4/4 time, each bar has 4 beats. A quarter note equals 1 beat.

**Example:** In 4/4 at 120 BPM, each beat is 0.5 seconds long.

### Tempo (BPM)
Beats Per Minute - the speed of the music. Higher BPM = faster music.

**Common tempos:**
- Largo: 40-60 BPM (very slow)
- Andante: 76-108 BPM (walking pace)
- Moderato: 108-120 BPM (moderate)
- Allegro: 120-168 BPM (fast)
- Presto: 168-200 BPM (very fast)

### Time Signature (Meter)
Defines how many beats are in each bar and what note value gets one beat.

**Format:** numerator/denominator
- **4/4** (common time): 4 beats per bar, quarter note = 1 beat
- **3/4** (waltz): 3 beats per bar, quarter note = 1 beat
- **6/8**: 6 beats per bar, eighth note = 1 beat

### Key Signature
The set of sharps or flats that define the tonality of the music.

**Examples:**
- C major: No sharps or flats
- G major: F#
- Am (A minor): No sharps or flats (relative minor of C major)

### Pitch
The frequency of a note. In MIDI, pitch is represented as a number from 0-127.

**MIDI pitch reference:**
- Middle C (C4) = 60
- A440 (concert A) = 69
- Each semitone = +/- 1
- Each octave = +/- 12

### Duration
How long a note is held.

**Common durations in 4/4:**
- Whole note: 4 beats
- Half note: 2 beats
- Quarter note: 1 beat
- Eighth note: 0.5 beats
- Sixteenth note: 0.25 beats

### Rest
A period of silence in music. Rests have durations just like notes.

### Velocity
In MIDI, velocity represents how hard a key is pressed, typically interpreted as volume/dynamics.

**Range:** 0-127
- 0: Silent (note off)
- 40-60: Piano (soft)
- 70-90: Mezzo forte (medium)
- 100-127: Forte/fortissimo (loud)

### Articulation
How a note is played (e.g., staccato, legato, marcato).

**Examples:**
- **Staccato**: Short, detached
- **Legato**: Smooth, connected
- **Marcato**: Emphasized, accented
- **Spiccato**: Light, bouncing (strings)

## DSL Structural Terms

### Project
The top-level container for an entire composition. Contains all tracks, clips, and metadata.

**Structure:**
```json
{
  "project": {
    "name": "...",
    "tracks": {...},
    "clip_library": [...]
  }
}
```

### Track
A parallel musical line, typically assigned to one instrument. Tracks reference clips at specific bar positions.

**Think of tracks as:**
- Horizontal timelines
- Separate instrument parts
- Parallel layers of music

**Example tracks:**
- "melody" track: lead vocal line
- "bass" track: bass guitar
- "drums" track: percussion

### Clip
A reusable musical pattern containing notes and rests. Clips are stored in the `clip_library` and referenced by tracks.

**Purpose:**
- Reusability: Define once, use multiple times
- Organization: Group related notes together
- Variation: Apply different expressions to the same notes

### Clip Library
A collection of all clips used in the project. Each clip has a unique `clip_id`.

**Analogy:** Like a palette of paint colors - define your colors once, use them many times.

### Clip Instance
A specific usage of a clip in a track at a particular bar position. Multiple instances can reference the same clip.

**Example:**
```json
{"clip_instance_id": "verse_1", "clip_id": 10, "start_bar": 1, "length_bars": 4}
{"clip_instance_id": "verse_2", "clip_id": 10, "start_bar": 9, "length_bars": 4}
```
Both instances use clip 10, but at different positions.

### Clip ID
Unique integer identifier for a clip in the clip_library.

**Must be unique** across all clips in a project.

### Clip Instance ID
Unique string identifier for a specific usage of a clip in a track. Used for tracking and debugging.

**Example:** "verse_1", "chorus_intro", "bass_pattern_a"

### Start Bar
The bar number where a clip instance begins playing (1-based).

**Note:** Bar 1 is the first bar of the composition.

### Length Bars
How many bars of a clip to play in a clip instance.

**If a clip has 4 bars but length_bars is 2:**
Only the first 2 bars of the clip will play.

**If length_bars is 8 but clip only has 4 bars:**
The clip bars repeat: bars 0,1,2,3,0,1,2,3

### Bar Index
Position of a bar within a clip (0-based).

**Important distinction:**
- **start_bar**: Absolute position in composition (1-based)
- **bar_index**: Relative position within a clip (0-based)

**Example:**
```
Clip has bars: [bar_index: 0], [bar_index: 1], [bar_index: 2]
Used at: start_bar: 5
Results in: composition bars 5, 6, 7
```

### Clip Bar
A single bar within a clip, containing notes relative to that bar.

## Expression Terms

### Bar Override
A way to add or modify expression curves for a specific bar in a clip instance without changing the original clip.

**Use cases:**
- Add crescendo to one instance of a repeated clip
- Vary dynamics between verses
- Add filter sweeps to specific sections

### Expression Curve
A series of time-value points that define how a parameter changes over time.

**Example velocity curve:**
```json
[
  {"time": 0.0, "value": 70},   // Start soft
  {"time": 2.0, "value": 110},  // Crescendo
  {"time": 4.0, "value": 80}    // Diminuendo
]
```

### Velocity Curve
An expression curve that controls dynamics (volume) over time within a bar.

**Effect:** Creates crescendos, diminuendos, accents

### CC (Control Change)
MIDI messages that control various parameters of a synthesizer or instrument.

**Common CC numbers:**
- CC 1: Modulation wheel (vibrato depth)
- CC 7: Volume
- CC 10: Pan (left-right position)
- CC 11: Expression (dynamics)
- CC 64: Sustain pedal
- CC 71: Filter resonance
- CC 74: Filter cutoff

### CC Lanes
Multiple CC curves organized by CC number.

**Example:**
```json
"cc_lanes": {
  "1": [...],   // Modulation
  "11": [...],  // Expression
  "74": [...]   // Filter
}
```

### Pitch Bend
Continuous pitch change, typically used for slides and vibrato. Measured in semitones or cents.

**Range:** Typically +/- 2 semitones (200 cents)
- 0: No bend
- 100: +1 semitone
- -100: -1 semitone

### Aftertouch (Channel Pressure)
Pressure applied after a key is pressed, often used for vibrato or dynamic swells.

### Pedal Events
Sustain pedal on/off events. When on, notes continue ringing after release.

## Technical Terms

### Ticks Per Quarter (TPPQ)
MIDI resolution - how many timing subdivisions exist per quarter note.

**Common values:**
- 96: Low resolution
- 480: Standard (recommended)
- 960: High resolution

**Higher = more precise timing**

### MIDI Channel
MIDI supports 16 independent channels (0-15), each can have a different instrument.

**Usage:**
```json
"tracks": {
  "piano": {"instrument": {"midi_channel": 0}},
  "bass": {"instrument": {"midi_channel": 1}},
  "drums": {"instrument": {"midi_channel": 9}}  // Channel 9 = drums by convention
}
```

### Start Beat
Position within a clip where a note starts, in beats from the beginning of the clip.

**For a note in the second bar:**
- Bar 1 occupies beats 0.0-4.0
- Bar 2 starts at beat 4.0
- Note at start of bar 2: `start_beat: 4.0`

### Duration Beats
Length of a note in beats.

**Examples in 4/4:**
- Whole note: 4.0
- Half note: 2.0
- Quarter note: 1.0
- Eighth note: 0.5
- Dotted quarter: 1.5
- Triplet quarter: 0.667

### Tempo Map
A list of tempo changes throughout the composition.

**Example:**
```json
[
  {"bar": 1, "tempo_bpm": 100},   // Start slow
  {"bar": 9, "tempo_bpm": 140}    // Speed up at bar 9
]
```

### Meter Map
A list of time signature changes throughout the composition.

**Example:**
```json
[
  {"bar": 1, "numerator": 4, "denominator": 4},  // 4/4 time
  {"bar": 9, "numerator": 3, "denominator": 4}   // Switch to 3/4
]
```

### Key Map
A list of key signature changes throughout the composition.

**Example:**
```json
[
  {"bar": 1, "key": "C", "mode": "major"},
  {"bar": 9, "key": "Am", "mode": "minor"}
]
```

### Loop
A repeating section of music defined by start bar, length, and repeat count.

**Example:**
```json
{"start_bar": 5, "length_bars": 4, "repeat_count": 2}
```
Bars 5-8 play 3 times total (original + 2 repeats).

## AST (Abstract Syntax Tree) Terms

### Composition AST
The parsed representation of a project after DSL parsing. Contains tracks, tempo, and metadata.

### Track AST
A parsed track containing an array of `TrackBarRef` objects.

### TrackBarRef
A reference that maps a composition bar to a specific clip and clip bar.

**Structure:**
```python
{
  "bar_index": 5,          # Composition bar
  "clip_id": 10,           # Which clip
  "clip_bar_index": 0      # Which bar in the clip
}
```

### ClipBar
A single bar within a clip, containing notes and optional expression curves.

### Database Format
The normalized output from the parser, ready to be stored in a database with separate tables for compositions, tracks, clips, and bars.

## Workflow Terms

### DSL Parser
The Python module (`dsl_parser.py`) that converts DSL JSON into AST models.

### Database-Ready Format
The output from `parser.to_database_format()` - a dictionary with separate arrays for compositions, clips, and tracks.

### MIDI Builder
The module that converts database format into MIDI events for playback.

### MIDI Player
The module that plays MIDI events through a synthesizer or sound output.

## Common Abbreviations

- **BPM**: Beats Per Minute
- **CC**: Control Change (MIDI)
- **MIDI**: Musical Instrument Digital Interface
- **DSL**: Domain-Specific Language
- **AST**: Abstract Syntax Tree
- **TPPQ**: Ticks Per Quarter Note
- **PPQ**: Pulses Per Quarter (same as TPPQ)
- **DAW**: Digital Audio Workstation

## Relationship Diagram

```
Project
├── Tracks (named)
│   └── Clip Instances
│       ├── References Clip (by clip_id)
│       ├── Placed at start_bar
│       └── Optional bar_overrides
└── Clip Library
    └── Clips (by clip_id)
        └── Clip Bars (by bar_index)
            └── Notes (by start_beat)
```

## Examples

### Complete Term Usage

```json
{
  "project": {                          // PROJECT
    "name": "my_song",
    "tempo_map": [                      // TEMPO MAP
      {"bar": 1, "tempo_bpm": 120}      // TEMPO (BPM)
    ],
    "meter_map": [                      // METER MAP
      {"bar": 1, "numerator": 4, "denominator": 4}  // TIME SIGNATURE
    ],
    "tracks": {                         // TRACKS
      "melody": {                       // TRACK NAME
        "instrument": {
          "midi_channel": 0             // MIDI CHANNEL
        },
        "clips": [                      // CLIP INSTANCES
          {
            "clip_instance_id": "m1",   // CLIP INSTANCE ID
            "clip_id": 1,               // CLIP ID (reference)
            "start_bar": 1,             // START BAR (absolute)
            "length_bars": 1,           // LENGTH BARS
            "bar_overrides": [          // BAR OVERRIDES
              {
                "bar_index": 0,         // BAR INDEX (relative)
                "velocity_curve": [     // VELOCITY CURVE
                  {"time": 0.0, "value": 90}
                ],
                "cc_lanes": {           // CC LANES
                  "1": [{"time": 0, "value": 64}]
                }
              }
            ]
          }
        ]
      }
    },
    "clip_library": [                   // CLIP LIBRARY
      {
        "clip_id": 1,                   // CLIP ID (definition)
        "name": "riff",                 // CLIP NAME
        "notes": [                      // NOTES
          {
            "pitch": 60,                // PITCH (MIDI note)
            "start_beat": 0.0,          // START BEAT (relative to clip)
            "duration_beats": 1.0       // DURATION BEATS
          },
          {
            "is_rest": true,            // REST
            "start_beat": 2.0,
            "duration_beats": 1.0
          }
        ]
      }
    ]
  }
}
```
