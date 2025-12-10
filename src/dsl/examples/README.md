# OSC DSL Examples

This directory contains progressive examples demonstrating the OSC DSL features from simple to complex.

## Files

### 01-simple-melody.json
**Difficulty:** Beginner
**Demonstrates:**
- Minimal project structure
- Single track with one instrument
- Basic clip with 4 notes (C major scale)
- Standard tempo, meter, and key setup

**Use this to learn:**
- Required project structure
- How to define a clip
- How to reference a clip in a track
- Basic note placement with pitch, start_beat, and duration_beats

---

### 02-multi-track.json
**Difficulty:** Beginner+
**Demonstrates:**
- Multiple tracks (melody and bass)
- Multiple clips per track
- Clips placed at different bar positions
- Notes spanning multiple bars
- Using rests in patterns

**Use this to learn:**
- How to arrange multiple tracks in parallel
- Sequential clip placement (verse → chorus)
- Creating a walking bass line
- Coordinating different instruments

---

### 03-expressions.json
**Difficulty:** Intermediate
**Demonstrates:**
- Bar-level expression overrides
- Velocity curves (crescendo/diminuendo)
- Multiple CC automation lanes (modulation, filter)
- Pitch bend curves
- Custom metadata tags

**Use this to learn:**
- How to add dynamics to repeated clips
- Creating expressive filter sweeps
- Combining multiple expression types
- Adding section markers with metadata

---

### 04-complete-song.json
**Difficulty:** Advanced
**Demonstrates:**
- Full song structure (intro, verse, chorus, bridge, outro)
- Three parallel tracks (melody, bass, pads)
- Tempo changes (100 → 120 BPM)
- Key changes (C major → F major)
- Clip reuse across sections
- Bar overrides for variation
- Loop regions
- Chord pads (sustained notes)

**Use this to learn:**
- How to structure a complete song
- Reusing clips with variations
- Coordinating multiple instruments
- Creating arrangement with dynamics
- Using tempo and key changes effectively

## Running the Examples

### Using the Parser

```python
from src.dsl.dsl_parser import parse_dsl_file

# Parse an example
composition = parse_dsl_file("examples/01-simple-melody.json")

# Convert to database format
from src.dsl.dsl_parser import DSLParser
parser = DSLParser()
composition = parser.parse_project(dsl_json)
db_format = parser.to_database_format(composition)
```

### Testing

All examples can be validated with the parser:

```bash
cd /Users/chrislomeli/Source/PycharmProjects/OSC
python src/dsl/dsl_parser.py < src/dsl/examples/01-simple-melody.json
```

## Tips for Creating Your Own

1. **Start Simple:** Begin with example 01, modify the notes, then build from there
2. **Use MIDI Reference:** Middle C = 60, each semitone = ±1, each octave = ±12
3. **Check Timing:** In 4/4 time, each bar is 4.0 beats. Notes must fit within bar boundaries
4. **Unique IDs:** Ensure all `clip_id` values are unique across the clip_library
5. **Test Incrementally:** Add one track or clip at a time, test, then expand

## Common MIDI Note Numbers

| Note | MIDI | Frequency |
|------|------|-----------|
| C2   | 36   | Bass      |
| C3   | 48   | Low       |
| C4   | 60   | Middle C  |
| A4   | 69   | 440 Hz    |
| C5   | 72   | High      |

## Musical Structure Reference

Common song structures you can create:

- **Simple:** Intro - Verse - Chorus - Outro
- **Standard:** Intro - Verse - Chorus - Verse - Chorus - Bridge - Chorus - Outro
- **Extended:** Intro - Verse 1 - Pre-Chorus - Chorus - Verse 2 - Pre-Chorus - Chorus - Bridge - Chorus - Outro

## Next Steps

After understanding these examples:
1. Read [../README.md](../README.md) for complete documentation
2. Check [../GLOSSARY.md](../GLOSSARY.md) for term definitions
3. Review [../DSL.md](../DSL.md) for the full specification
4. Explore the test suite in `../tests/test_dsl_parser.py`

## Questions?

If you're unsure about something:
1. Check the inline comments in the example files
2. Refer to the main README.md
3. Look up terms in GLOSSARY.md
4. Review the DSL.md specification
