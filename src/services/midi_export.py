from typing import Any, Dict, List, Optional

import mido


def composition_db_dict_to_midi_bytes(data: Dict[str, Any], include_all_tracks: bool = True) -> bytes:
    """Convert a DSL/DB-style composition dict to MIDI file bytes.

    Expected input format (matches DSLParser.to_database_format output):

    {
      "composition": {"name": str, "ticks_per_quarter": int, "tempo_bpm": int},
      "clips": [
        {
          "id": int,
          "name": str,
          "track_name": str | None,
          "bars": [
            {
              "clip_id": int,
              "bar_index": int,
              "notes": [
                {
                  "absolute_pitch": int,
                  "start": float,        # beats, relative to bar
                  "duration": float,     # beats
                  "is_rest": bool,
                  # ... optional semantics
                }
              ],
              "velocity_curve": [...],   # optional; list[{"time": float, "value": int}]
              # "cc", "pitch_bend_curve", etc. are currently ignored
            }
          ]
        }
      ],
      "tracks": [
        {
          "name": str,
          "bars": [
            {"bar_index": int, "clip_id": int, "clip_bar_index": int}
          ]
        }
      ]
    }
    """

    comp_meta = data["composition"]
    clips = data.get("clips", [])
    tracks = data.get("tracks", [])

    ticks_per_beat = int(comp_meta.get("ticks_per_quarter", 480))
    tempo_bpm = int(comp_meta.get("tempo_bpm", 120))

    # Map clips by id for quick lookup
    clips_by_id: Dict[int, Dict[str, Any]] = {c["id"]: c for c in clips}

    mid = mido.MidiFile(ticks_per_beat=ticks_per_beat)

    # For now assume 4/4 (4 beats per bar) consistently.
    beats_per_bar = 4.0

    # Create one MIDI track per logical track
    for track_index, track_data in enumerate(tracks):
        track = mido.MidiTrack()
        mid.tracks.append(track)

        # Set track name
        track.append(mido.MetaMessage("track_name", name=track_data.get("name", f"Track {track_index+1}"), time=0))

        # Only set tempo on the first track
        if track_index == 0:
            tempo = mido.bpm2tempo(tempo_bpm)
            track.append(mido.MetaMessage("set_tempo", tempo=tempo, time=0))

        # Collect absolute-time events in ticks
        events: List[tuple[int, mido.Message]] = []

        # Assign MIDI channel per track (0-15)
        channel = track_index % 16

        for bar_ref in track_data.get("bars", []):
            bar_index = int(bar_ref["bar_index"])  # 1-based
            clip_id = int(bar_ref["clip_id"])
            clip_bar_index = int(bar_ref["clip_bar_index"])  # 0-based index into clip.bars

            clip = clips_by_id.get(clip_id)
            if not clip:
                continue

            clip_bars = clip.get("bars", [])
            if clip_bar_index < 0 or clip_bar_index >= len(clip_bars):
                continue

            bar = clip_bars[clip_bar_index]
            bar_start_beats = (bar_index - 1) * beats_per_bar

            velocity_curve = bar.get("velocity_curve")

            for note in bar.get("notes", []):
                if note.get("is_rest", False):
                    continue

                pitch = int(note.get("absolute_pitch", 0))
                start_beats = float(note.get("start", 0.0))
                duration_beats = float(note.get("duration", 1.0))

                note_start_beats = bar_start_beats + start_beats
                note_end_beats = note_start_beats + duration_beats

                # Very simple velocity handling: interpolate from bar-level velocity curve if present
                velocity = _interpolate_curve(velocity_curve, start_beats) if velocity_curve else 100
                if velocity is None:
                    velocity = 100

                start_ticks = int(round(note_start_beats * ticks_per_beat))
                end_ticks = int(round(note_end_beats * ticks_per_beat))

                on = mido.Message("note_on", note=pitch, velocity=velocity, channel=channel, time=0)
                off = mido.Message("note_off", note=pitch, velocity=0, channel=channel, time=0)

                events.append((start_ticks, on))
                events.append((end_ticks, off))

        # Sort events by absolute tick and convert to delta times
        events.sort(key=lambda item: item[0])
        last_tick = 0
        for abs_tick, msg in events:
            delta = abs_tick - last_tick
            msg.time = max(0, delta)
            track.append(msg)
            last_tick = abs_tick

    # Serialize to bytes
    from io import BytesIO

    buf = BytesIO()
    mid.save(file=buf)
    return buf.getvalue()


def _interpolate_curve(curve: List[Dict[str, Any]], target_time: float) -> Optional[int]:
    """Linear interpolation helper matching MidiClipPlayer semantics for velocity curves."""

    if not curve:
        return None

    times = [float(p["time"]) for p in curve]
    values = [float(p["value"]) for p in curve]

    if target_time <= times[0]:
        return int(values[0])
    if target_time >= times[-1]:
        return int(values[-1])

    # Find rightmost value less than or equal to target_time
    import bisect

    idx = bisect.bisect_right(times, target_time)
    t0, t1 = times[idx - 1], times[idx]
    v0, v1 = values[idx - 1], values[idx]

    if t1 == t0:
        return int(v0)

    ratio = (target_time - t0) / (t1 - t0)
    return int(v0 + (v1 - v0) * ratio)
