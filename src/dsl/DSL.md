

# DSL 
```json
{
  "project": {
    "name": "phrase_loop_example",
    "ticks_per_quarter": 480,
    "tempo_map": [
      { "bar": 1, "tempo_bpm": 120 }
    ],
    "meter_map": [
      { "bar": 1, "numerator": 4, "denominator": 4 }
    ],
    "key_map": [
      { "bar": 1, "key": "C", "mode": "major" }
    ],

    "tracks": {
      "lead": {
        "instrument": {
          "name": "lead-kazoo",
          "midi_channel": 0
        },
        "clips": [
          {
            "clip_instance_id": "lead_1",
            "clip_id": 8,
            "start_bar": 1,
            "length_bars": 2,
            "bar_overrides": [
              {
                "bar_index": 1,
                "velocity_curve": [
                  { "time": 0, "value": 90 },
                  { "time": 4, "value": 100 }
                ],
                "cc_lanes": {
                  "1": [
                    { "time": 0, "value": 64 }
                  ]
                },
                "pitch_bend_curve": [
                  { "time": 0, "value": 0 },
                  { "time": 4, "value": 200 }
                ],
                "aftertouch_curve": null,
                "pedal_events": null,
                "metadata": {
                  "tag": "intro"
                }
              }
            ]
          }
        ]
      },

      "bass": {
        "instrument": {
          "name": "bass-kazoo",
          "midi_channel": 1
        },
        "clips": [
          {
            "clip_instance_id": "bass_1",
            "clip_id": 10,
            "start_bar": 1,
            "length_bars": 2
          }
        ]
      }
    },

    "loops": [
      {
        "start_bar": 5,
        "length_bars": 4,
        "repeat_count": 1
      }
    ],

    "clip_library": [
      {
        "clip_id": 8,
        "name": "lead-riff-intro",
        "style": "latin",
        "notes": [
          { "pitch": 60, "start_beat": 0.0,  "duration_beats": 1.0 },
          { "pitch": 64, "start_beat": 1.0,  "duration_beats": 1.0 },
          { "pitch": 67, "start_beat": 2.0,  "duration_beats": 1.0 },
          { "is_rest": true, "start_beat": 3.0, "duration_beats": 1.0 }
        ]
      },
      {
        "clip_id": 9,
        "name": "lead-riff-bridge",
        "style": "latin",
        "notes": [
          { "pitch": 60, "start_beat": 0.0,  "duration_beats": 1.0 },
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
          { "pitch": 48, "start_beat": 0.0, "duration_beats": 1.0 },
          { "pitch": 46, "start_beat": 1.0, "duration_beats": 1.0 },
          { "pitch": 72, "start_beat": 2.0, "duration_beats": 1.0 },
          { "is_rest": true, "start_beat": 3.0, "duration_beats": 1.0 }
        ]
      }
    ]
  }
}

```



# Design

```aiignore
Project {
  ticks_per_quarter
  tempo_map[]
  meter_map[]
  key_map[]
  tracks: {
    track_name: Track
  }
  loops[]
}

```

## Track
```aiignore
Track {
  instrument: {
    name
    midi_channel
    expression_profile
  }
  clips: [Clip]
}

```

## Clip
```aiignore
Clip {
  clip_id
  start_bar
  length_bars
  notes: [NoteEvent]
  cc_lanes: CC[]
  pitch_bend_curve: Curve
  aftertouch_curve: Curve
}

```

## NoteEvent
```aiignore
NoteEvent {
    pitch
    start_beat
    duration_beats
    velocity
    articulation   // staccato, spiccato, marcato, legato
    expression: {
        vibrato_depth
        vibrato_rate
        cents_offset
    }
    semantics: {
        scale_degree
        interval_from_prev
    }
}


```_


## Legacy

### Create three clips
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



