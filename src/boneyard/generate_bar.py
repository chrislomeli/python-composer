# from src.schema.voice_bar import VoiceBar
# from src.schema.note import Note
#
# def generate_bar(bar_number, note_sequence, grid_units=32):
#     """
#     note_sequence: list of dicts
#       e.g., [
#         {"pitch_name": "C", "octave": 4, "duration_units": 8},
#         {"pitch_name": "Db", "octave": 4, "duration_units": 8},
#         {"pitch_name": "A", "octave": 3, "duration_units": 8},
#         {"pitch_name": "C", "octave": 4, "duration_units": 8, "is_rest": True},
#       ]
#     """
#     bar = VoiceBar(bar_number, grid_units=grid_units)
#     current_unit = 0
#     for n in note_sequence:
#         note = Note(
#             pitch_name=n.get("pitch_name"),
#             octave=n.get("octave"),
#             duration_units=n.get("duration_units"),
#             is_rest=n.get("is_rest", False),
#             velocity=n.get("velocity", 90),
#             articulation=n.get("articulation", "normal")
#         )
#         # set the start_unit relative to the bar
#         note.start_unit = current_unit
#         current_unit += note.duration_units
#
#         # check overflow
#         if current_unit > grid_units:
#             raise ValueError(f"Note durations exceed grid_units ({grid_units}) in bar {bar_number}")
#
#         bar.add_note(note)
#
#     return bar
#
#
