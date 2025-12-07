from src.repo.composition_repo import CompositionRepo
from src.repo.models import CompositionModel, TrackModel, TrackBarModel, ClipBarModel
from src.repo.track_repo import TrackRepo
from src.repo.track_bar_repo import TrackBarRepo
from src.repo.clip_bar_repo import ClipBarRepo
from typing import Dict

async def load_composition(session, composition_json: Dict) -> int:
    comp_repo = CompositionRepo(session)
    track_repo = TrackRepo(session)
    track_bar_repo = TrackBarRepo(session)
    clip_bar_repo = ClipBarRepo(session)

    async def place_clip(track_id: int, clip_ref: Dict, start_offset: int = 0):
        """
        Place clip into track_bar table, optionally shifted by start_offset (used for loops)
        Also insert optional clip_bars into clip_bar table
        """
        start_bar = clip_ref["start_bar"] + start_offset
        length = clip_ref["length_in_bars"]

        # 1. TrackBar entries
        for i in range(length):
            tb_model = TrackBarModel(
                track_id=track_id,
                bar_index=start_bar + i,
                clip_id=clip_ref["clip_id"],
                clip_bar_index=i,
                metadata=clip_ref.get("metadata")
            )
            await track_bar_repo.create_track_bar(tb_model)

        # 2. ClipBar entries
        for cb in clip_ref.get("clip_bars", []):
            cb_model = ClipBarModel(
                clip_id=clip_ref["clip_id"],
                bar_index=cb["bar_index"] + start_offset,
                velocity_curve=cb.get("velocity_curve"),
                cc=cb.get("cc"),
                pitch_bend_curve=cb.get("pitch_bend_curve"),
                aftertouch_curve=cb.get("aftertouch_curve"),
                pedal_events=cb.get("pedal_events"),
                metadata=cb.get("metadata")
            )
            await clip_bar_repo.create_clip_bar(cb_model)

    # 1. Create composition
    composition_id = await comp_repo.create_composition(
        CompositionModel(
            name=composition_json["name"],
            ticks_per_quarter=composition_json.get("ticks_per_quarter", 480),
            tempo_bpm=composition_json.get("tempo_bpm", 120)
        )
    )

    # 2. Create tracks and insert clips
    track_ids = {}
    for track_name, clips in composition_json["tracks"].items():
        track_model = TrackModel(
            composition_id=composition_id,
            name=track_name,
            instrument=clips[0].get("instrument") if clips else None
        )
        track_id = await track_repo.create_track(track_model)
        track_ids[track_name] = track_id

        for clip_ref in clips:
            await place_clip(track_id, clip_ref)

    # 3. Handle loops
    for loop in composition_json.get("loops", []):
        start_bar = loop["start_bar"]
        length = loop["length_in_bars"]
        repeat = loop["repeat_count"]

        for r in range(repeat):
            for track_name, clips in composition_json["tracks"].items():
                track_id = track_ids[track_name]
                for clip_ref in clips:
                    clip_start = clip_ref["start_bar"]
                    clip_end = clip_start + clip_ref["length_in_bars"] - 1

                    # Only copy clips that overlap the loop range
                    if clip_start < start_bar + length:
                        await place_clip(track_id, clip_ref, start_offset=start_bar + r * length - clip_start)

    return composition_id
