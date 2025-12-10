import time
import bisect
import mido


class MidiClipPlayer:
    def __init__(self, midi_port_name=None, fluidsynth=None, bpm=120, beats_per_bar=4, loop=False):
        """
        midi_port_name: string, MIDI output port via mido (optional)
        fluidsynth: pyFluidSynth.Synth instance (optional)
        bpm: tempo in beats per minute
        beats_per_bar: usually 4
        loop: if True, loop clip
        """
        if not midi_port_name and not fluidsynth:
            raise ValueError("Must provide either midi_port_name or fluidsynth instance")

        self.out_port = mido.open_output(midi_port_name) if midi_port_name else None
        self.fs = fluidsynth  # pyFluidSynth synth instance
        self.bpm = bpm
        self.beat_duration = 60.0 / bpm
        self.beats_per_bar = beats_per_bar
        self.loop = loop

    def _interpolate_curve(self, curve, target_time):
        if not curve:
            return None
        times = [p['time'] for p in curve]
        values = [p['value'] for p in curve]
        if target_time <= times[0]:
            return values[0]
        if target_time >= times[-1]:
            return values[-1]
        idx = bisect.bisect_right(times, target_time)
        t0, t1 = times[idx - 1], times[idx]
        v0, v1 = values[idx - 1], values[idx]
        ratio = (target_time - t0) / (t1 - t0)
        return int(v0 + (v1 - v0) * ratio)

    def _schedule_events(self, clip):
        events = []

        for bar in clip.get("bars", []):
            bar_start_time = bar["bar_index"] * self.beats_per_bar * self.beat_duration

            # CC
            if bar.get("cc"):
                for cc_event in bar["cc"]:
                    cc_time = bar_start_time + cc_event["time"] * self.beat_duration
                    events.append((cc_time, 'cc', cc_event["controller"], cc_event["value"]))

            # Pitch bend and aftertouch curves
            pb_curve = bar.get("pitch_bend_curve")
            at_curve = bar.get("aftertouch_curve")

            # Pedal
            if bar.get("pedal_events"):
                for ped in bar["pedal_events"]:
                    ped_time = bar_start_time + ped["time"] * self.beat_duration
                    events.append((ped_time, 'cc', ped["controller"], ped["value"]))

            # Notes
            for note in bar.get("notes", []):
                if note.get("is_rest", False):
                    continue
                pitch = note["pitch"]
                start_time = bar_start_time + note["start_beat"] * self.beat_duration
                duration = note["duration_beats"] * self.beat_duration

                # velocity
                velocity = self._interpolate_curve(bar.get("velocity_curve"), note["start_beat"])
                if velocity is None:
                    velocity = 100

                events.append((start_time, 'note_on', pitch, velocity))
                events.append((start_time + duration, 'note_off', pitch, 0))

                # Pitch bend during note
                if pb_curve:
                    steps = 10
                    for i in range(steps):
                        t_beat = note["start_beat"] + (i / steps) * note["duration_beats"]
                        pb_value = self._interpolate_curve(pb_curve, t_beat)
                        if pb_value is not None:
                            t_sec = bar_start_time + t_beat * self.beat_duration
                            events.append((t_sec, 'pitch_bend', None, pb_value))

                # Aftertouch
                if at_curve:
                    steps = 10
                    for i in range(steps):
                        t_beat = note["start_beat"] + (i / steps) * note["duration_beats"]
                        at_value = self._interpolate_curve(at_curve, t_beat)
                        if at_value is not None:
                            t_sec = bar_start_time + t_beat * self.beat_duration
                            events.append((t_sec, 'aftertouch', pitch, at_value))

        events.sort(key=lambda x: x[0])
        return events

    def _send_message(self, kind, param1, param2):
        if self.out_port:
            if kind == 'note_on':
                msg = mido.Message('note_on', note=param1, velocity=param2)
            elif kind == 'note_off':
                msg = mido.Message('note_off', note=param1, velocity=param2)
            elif kind == 'cc':
                msg = mido.Message('control_change', control=param1, value=param2)
            elif kind == 'pitch_bend':
                msg = mido.Message('pitchwheel', pitch=param2)
            elif kind == 'aftertouch':
                msg = mido.Message('aftertouch', value=param2)
            else:
                return
            self.out_port.send(msg)
        elif self.fs:
            if kind == 'note_on':
                self.fs.noteon(0, param1, param2)
            elif kind == 'note_off':
                self.fs.noteoff(0, param1)
            elif kind == 'cc':
                self.fs.cc(0, param1, param2)
            elif kind == 'pitch_bend':
                # pyFluidSynth pitch bend uses 14-bit value -8192..8191
                self.fs.pitch_bend(0, param2 - 8192)
            elif kind == 'aftertouch':
                self.fs.channel_pressure(0, param2)

    def play_dsl_clip(self, clip):
        while True:
            events = self._schedule_events(clip)
            start_time = time.time()
            for event_time, kind, param1, param2 in events:
                now = time.time()
                delay = (start_time + event_time) - now
                if delay > 0:
                    time.sleep(delay)
                self._send_message(kind, param1, param2)
            if not self.loop:
                break
