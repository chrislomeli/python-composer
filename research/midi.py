"""
Algorithmic Composition Starter Template
Combines mido (MIDI file creation) with music21 (music theory)

Install:
    pip install mido music21

Author: Your Name
Date: 2024
"""

from mido import MidiFile, MidiTrack, Message, MetaMessage
from music21 import note, chord, scale, stream, interval
import random

# =============================================================================
# CONFIGURATION
# =============================================================================

TICKS_PER_BEAT = 480  # Standard MIDI resolution
TEMPO_BPM = 120
OUTPUT_FILE = "my_composition.mid"


# =============================================================================
# MUSICAL TIME HELPERS
# =============================================================================

class MusicalTime:
    """Convert musical durations to MIDI ticks"""

    def __init__(self, ticks_per_beat=480):
        self.tpb = ticks_per_beat

    def whole(self): return self.tpb * 4

    def half(self): return self.tpb * 2

    def quarter(self): return self.tpb

    def eighth(self): return self.tpb // 2

    def sixteenth(self): return self.tpb // 4

    def dotted(self, duration): return int(duration * 1.5)

    def triplet(self, duration): return int(duration * 2 / 3)


mt = MusicalTime(TICKS_PER_BEAT)


# =============================================================================
# MUSIC21 HELPERS - Music Theory Operations
# =============================================================================

def get_scale_notes(root='C', octave=4, scale_type='major'):
    """
    Get notes from a scale using music21

    Args:
        root: Root note (C, D, E, etc.)
        octave: Octave number
        scale_type: 'major', 'minor', 'dorian', etc.

    Returns:
        List of MIDI note numbers
    """
    if scale_type == 'major':
        s = scale.MajorScale(f'{root}{octave}')
    elif scale_type == 'minor':
        s = scale.MinorScale(f'{root}{octave}')
    elif scale_type == 'dorian':
        s = scale.DorianScale(f'{root}{octave}')
    else:
        s = scale.MajorScale(f'{root}{octave}')

    # Get one octave of pitches
    pitches = s.getPitches(f'{root}{octave}', f'{root}{octave + 1}')

    # Convert to MIDI note numbers
    return [p.midi for p in pitches]


def get_chord_notes(chord_symbol, octave=4):
    """
    Get notes from a chord using music21

    Args:
        chord_symbol: 'C', 'Dm', 'G7', 'Am7', etc.
        octave: Base octave

    Returns:
        List of MIDI note numbers
    """
    # Parse chord symbol
    c = chord.Chord(f'{chord_symbol}{octave}')
    return [p.midi for p in c.pitches]


def transpose_notes(notes, semitones):
    """Transpose a list of MIDI notes by semitones"""
    return [n + semitones for n in notes]


def get_interval_from_note(note_num, interval_name):
    """
    Get a note at a specific interval from a given note

    Args:
        note_num: MIDI note number
        interval_name: 'P5' (perfect 5th), 'M3' (major 3rd), etc.

    Returns:
        MIDI note number
    """
    n = note.Note()
    n.midi = note_num

    i = interval.Interval(interval_name)
    transposed = n.transpose(i)

    return transposed.midi


# =============================================================================
# MIDO HELPERS - MIDI File Creation
# =============================================================================

def create_midi_file():
    """Create a new MIDI file with tempo"""
    mid = MidiFile(ticks_per_beat=TICKS_PER_BEAT)

    # Tempo track
    tempo_track = MidiTrack()
    mid.tracks.append(tempo_track)

    # Set tempo (microseconds per beat)
    tempo_us = int(60_000_000 / TEMPO_BPM)
    tempo_track.append(MetaMessage('set_tempo', tempo=tempo_us, time=0))

    return mid


def add_note_to_track(track, note_num, velocity, start_tick, duration_ticks, channel=0):
    """
    Add a note to a track (handles delta time calculation)

    Args:
        track: MidiTrack object
        note_num: MIDI note number (0-127)
        velocity: Note velocity (0-127)
        start_tick: Absolute tick position for note start
        duration_ticks: How long the note lasts
        channel: MIDI channel (0-15)
    """
    track.append(Message('note_on', note=note_num, velocity=velocity,
                         time=start_tick, channel=channel))
    track.append(Message('note_off', note=note_num, velocity=0,
                         time=duration_ticks, channel=channel))


def add_chord_to_track(track, notes, velocity, start_tick, duration_ticks, channel=0):
    """Add a chord (multiple simultaneous notes)"""
    for i, note_num in enumerate(notes):
        track.append(Message('note_on', note=note_num, velocity=velocity,
                             time=start_tick if i == 0 else 0, channel=channel))

    for i, note_num in enumerate(notes):
        track.append(Message('note_off', note=note_num, velocity=0,
                             time=duration_ticks if i == 0 else 0, channel=channel))


# =============================================================================
# ALGORITHMIC COMPOSITION FUNCTIONS
# =============================================================================

def generate_random_melody(scale_notes, num_notes=8, note_duration=None):
    """
    Generate a random melody constrained to a scale

    Args:
        scale_notes: List of MIDI note numbers from a scale
        num_notes: How many notes to generate
        note_duration: Duration in ticks (default: quarter note)

    Returns:
        List of (note, duration) tuples
    """
    if note_duration is None:
        note_duration = mt.quarter()

    melody = []
    for _ in range(num_notes):
        note_num = random.choice(scale_notes)
        melody.append((note_num, note_duration))

    return melody


def generate_random_walk_melody(scale_notes, num_notes=8, max_jump=2):
    """
    Generate melody using random walk (smoother than pure random)

    Args:
        scale_notes: List of MIDI note numbers
        num_notes: How many notes
        max_jump: Maximum interval jump in scale degrees
    """
    melody = []
    current_index = len(scale_notes) // 2  # Start in middle of scale

    for _ in range(num_notes):
        melody.append((scale_notes[current_index], mt.quarter()))

        # Random walk: move up or down by max_jump steps
        step = random.randint(-max_jump, max_jump)
        current_index = max(0, min(len(scale_notes) - 1, current_index + step))

    return melody


def generate_chord_progression(key='C', progression=['I', 'IV', 'V', 'I']):
    """
    Generate a chord progression

    Args:
        key: Root key
        progression: Roman numeral progression

    Returns:
        List of chord note lists
    """
    # Simple mapping (extend this for more chords)
    degree_to_chord = {
        'I': key,
        'ii': f'{key}m',
        'iii': f'{key}m',
        'IV': key,
        'V': key,
        'vi': f'{key}m',
        'vii': f'{key}dim'
    }

    chords = []
    for degree in progression:
        # This is simplified - music21 has better chord parsing
        # For now, just use major triads
        chord_root = key
        chord_notes = get_chord_notes(chord_root, octave=4)
        chords.append(chord_notes)

    return chords


# =============================================================================
# EXAMPLE COMPOSITIONS
# =============================================================================

def example_1_simple_scale():
    """Example 1: Play a C major scale"""
    print("Creating Example 1: Simple Scale")

    mid = create_midi_file()
    track = MidiTrack()
    mid.tracks.append(track)
    track.append(MetaMessage('track_name', name='Melody', time=0))

    # Get C major scale using music21
    scale_notes = get_scale_notes('C', octave=4, scale_type='major')

    # Add notes to track
    current_tick = 0
    for note_num in scale_notes:
        add_note_to_track(track, note_num, velocity=80,
                          start_tick=current_tick,
                          duration_ticks=mt.quarter())
        current_tick += mt.quarter()

    mid.save('example_1_scale.mid')
    print("Saved: example_1_scale.mid")


def example_2_chords_and_melody():
    """Example 2: Chord progression with melody"""
    print("\nCreating Example 2: Chords and Melody")

    mid = create_midi_file()

    # Track 1: Chords
    chord_track = MidiTrack()
    mid.tracks.append(chord_track)
    chord_track.append(MetaMessage('track_name', name='Chords', time=0))

    # Track 2: Melody
    melody_track = MidiTrack()
    mid.tracks.append(melody_track)
    melody_track.append(MetaMessage('track_name', name='Melody', time=0))

    # Generate chord progression using music21
    c_major = get_chord_notes('C', octave=3)
    f_major = get_chord_notes('F', octave=3)
    g_major = get_chord_notes('G', octave=3)

    chords = [c_major, f_major, g_major, c_major]

    # Add chords (whole notes)
    current_tick = 0
    for chord_notes in chords:
        add_chord_to_track(chord_track, chord_notes, velocity=60,
                           start_tick=current_tick,
                           duration_ticks=mt.whole())
        current_tick += mt.whole()

    # Generate melody using music21 scale
    scale_notes = get_scale_notes('C', octave=5, scale_type='major')
    melody = generate_random_walk_melody(scale_notes, num_notes=16)

    # Add melody
    current_tick = 0
    for note_num, duration in melody:
        add_note_to_track(melody_track, note_num, velocity=80,
                          start_tick=current_tick,
                          duration_ticks=duration)
        current_tick += duration

    mid.save('example_2_chords_melody.mid')
    print("Saved: example_2_chords_melody.mid")


def example_3_algorithmic_composition():
    """Example 3: More complex algorithmic piece"""
    print("\nCreating Example 3: Algorithmic Composition")

    mid = create_midi_file()

    # Track 1: Bass line
    bass_track = MidiTrack()
    mid.tracks.append(bass_track)
    bass_track.append(MetaMessage('track_name', name='Bass', time=0))

    # Track 2: Melody
    melody_track = MidiTrack()
    mid.tracks.append(melody_track)
    melody_track.append(MetaMessage('track_name', name='Melody', time=0))

    # Use music21 for scale
    scale_notes = get_scale_notes('D', octave=4, scale_type='minor')
    bass_notes = get_scale_notes('D', octave=2, scale_type='minor')

    # Generate bass line (root notes on downbeats)
    current_tick = 0
    for _ in range(8):
        bass_note = bass_notes[0]  # Root note
        add_note_to_track(bass_track, bass_note, velocity=80,
                          start_tick=current_tick,
                          duration_ticks=mt.half())
        current_tick += mt.whole()

    # Generate melody with varying rhythms
    current_tick = 0
    rhythms = [mt.quarter(), mt.eighth(), mt.eighth(), mt.quarter(),
               mt.half(), mt.quarter(), mt.quarter()]

    for rhythm in rhythms * 4:  # Repeat pattern
        note_num = random.choice(scale_notes)
        add_note_to_track(melody_track, note_num, velocity=70,
                          start_tick=current_tick,
                          duration_ticks=int(rhythm * 0.9))  # Slight staccato
        current_tick += rhythm

    mid.save('example_3_algorithmic.mid')
    print("Saved: example_3_algorithmic.mid")


# =============================================================================
# YOUR COMPOSITION TEMPLATE
# =============================================================================

def my_composition():
    """
    YOUR COMPOSITION HERE

    This is your sandbox - experiment freely!
    Use music21 for theory, mido for MIDI output
    """
    print("\nCreating Your Composition")

    mid = create_midi_file()
    track = MidiTrack()
    mid.tracks.append(track)

    # TODO: Add your composition logic here
    # Examples:
    # 1. Get a scale: scale_notes = get_scale_notes('E', 4, 'minor')
    # 2. Get a chord: chord_notes = get_chord_notes('Am7', 3)
    # 3. Generate melody: melody = generate_random_walk_melody(scale_notes)
    # 4. Add to track: add_note_to_track(track, ...)

    # Placeholder: C major arpeggio
    arpeggio = get_chord_notes('C', octave=4)
    current_tick = 0
    for note_num in arpeggio:
        add_note_to_track(track, note_num, velocity=80,
                          start_tick=current_tick,
                          duration_ticks=mt.eighth())
        current_tick += mt.eighth()

    mid.save(OUTPUT_FILE)
    print(f"Saved: {OUTPUT_FILE}")



def play_examples():
    print("=" * 70)
    print("ALGORITHMIC COMPOSITION STARTER")
    print("=" * 70)

    # Run examples
    example_1_simple_scale()
    example_2_chords_and_melody()
    example_3_algorithmic_composition()

def run_my_composition():
    # Run your composition
    my_composition()


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("ALGORITHMIC COMPOSITION STARTER")
    print("=" * 70)

    # Run examples
    play_examples()

    # Run your composition
    run_my_composition()

    # print("\n" + "=" * 70)
    # print("All MIDI files created!")
    # print("Next steps:")
    # print("1. Open these files in Reaper or any MIDI player")
    # print("2. Listen and analyze what the code created")
    # print("3. Modify my_composition() to create your own music")
    # print("4. Experiment with the helper functions")
    # print("=" * 70)