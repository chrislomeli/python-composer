# src/repo/clip_loader.py
from typing import Dict
from src.repo.clip_repo import ClipRepo
from src.repo.note_repo import NoteRepo
from src.repo.models import ClipModel, NoteModel, VoiceBarModel
from src.repo.voice_bar_repo import VoiceBarRepo


class ClipBuilder:
    def __init__(self, clip_repo: ClipRepo, note_repo: NoteRepo, vb_repo: VoiceBarRepo):
        self.clip_repo = clip_repo
        self.note_repo = note_repo
        self.vb_repo = vb_repo

    async def load_clip_from_json(self, clip_data: dict) -> int:
        # Step 1: create ClipModel with defaults
        clip_model = ClipModel(**clip_data)
        clip_id = await self.clip_repo.create_clip(clip_model)

        # Step 2: create VoiceBars
        for vb_data in clip_data.get("voice_bars", []):
            vb_model = VoiceBarModel(
                clip_id=clip_id,
                bar_number=vb_data["bar_number"],
                time_signature_numerator=vb_data.get("time_signature_numerator", 4),
                time_signature_denominator=vb_data.get("time_signature_denominator", 4),
                metadata=vb_data.get("metadata"),
            )

            bar_id = await self.vb_repo.create_voice_bar(vb_model)

            # Step 3: create Notes
            for note_data in vb_data.get("notes", []):
                note_model = NoteModel(
                    bar_id=bar_id,
                    start_unit=note_data["start_unit"],
                    duration_units=note_data["duration_units"],
                    pitch_name=note_data.get("pitch_name"),
                    octave=note_data.get("octave"),
                    velocity=note_data.get("velocity", 90),
                    articulation=note_data.get("articulation", "normal"),
                    is_rest=note_data.get("is_rest", False),
                    expression=note_data.get("expression"),
                    microtiming_offset=note_data.get("microtiming_offset"),
                    metadata=note_data.get("metadata"),
                )
                await self.note_repo.create_note(note_model)

        return clip_id
