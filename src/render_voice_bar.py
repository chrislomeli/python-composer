from mido import Message

class BarRenderer:
    def __init__(self, ticks_per_quarter=480, units_per_quarter=8):
        self.ticks_per_quarter = ticks_per_quarter
        self.units_per_quarter = units_per_quarter

        # This defines unit → tick resolution:
        self.ticks_per_unit = self.ticks_per_quarter // self.units_per_quarter

    def render_bar(self, bar, start_midi_time=0):
        """
        Convert a Bar into a list of MIDI events with absolute ticks.
        bar.notes = list of Note objects (we defined earlier)
        start_midi_time = absolute tick offset for where this bar begins
        """

        events = []

        for note in bar.notes:
            # Skip rests — they create no MIDI events
            if note.is_rest:
                continue

            # Convert start + duration to ticks
            note_on_time = start_midi_time + (note.start_unit * self.ticks_per_unit)
            note_off_time = note_on_time + (note.duration_units * self.ticks_per_unit)

            # MIDI events
            events.append({
                "time": note_on_time,
                "message": Message('note_on',
                                   note=note.midi_pitch,
                                   velocity=note.velocity)
            })

            events.append({
                "time": note_off_time,
                "message": Message('note_off',
                                   note=note.midi_pitch,
                                   velocity=0)
            })

        # Sort by time, since events can arrive out of order
        events.sort(key=lambda e: e["time"])

        return events
