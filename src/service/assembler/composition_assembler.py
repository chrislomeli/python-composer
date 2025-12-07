from src.repo.clip_bar_repo import ClipBarRepo
from src.repo.clip_repo import ClipRepo
from src.repo.composition_repo import CompositionRepo
from src.repo.note_repo import NoteRepo
from src.repo.track_bar_repo import TrackBarRepo
from src.repo.track_repo import TrackRepo
from src.service.assembler.data_classes import Composition, TrackBarRef, Note, Bar, Clip, Track


class CompositionAssembler:
    def __init__(self, session):
        self.session = session

        self.comp_repo = CompositionRepo(session)
        self.track_repo = TrackRepo(session)
        self.track_bar_repo = TrackBarRepo(session)
        self.clip_repo = ClipRepo(session)          # you already have this
        self.clip_bar_repo = ClipBarRepo(session)   # and this
        self.note_repo = NoteRepo(session)

    async def load_composition(self, composition_id: int) -> Composition:
        # 1. Load composition metadata
        comp = await self.comp_repo.get_composition(composition_id)

        # 2. Load tracks
        tracks = await self.track_repo.get_tracks_for_composition(composition_id)

        # 3. Load track_bar rows for all tracks
        tbars_by_track = await self.track_bar_repo.get_by_tracks([t.id for t in tracks])

        # 4. Determine which clips are required
        clip_ids = {tb.clip_id for tb in tbars_by_track}

        # 5. Load clips + bars + notes
        clip_map = await self._load_clips(clip_ids)

        # 6. Build Track objects
        track_objs = []
        for t in tracks:
            our_tbars = [tb for tb in tbars_by_track if tb.track_id == t.id]

            track_objs.append(
                Track(
                    id=t.id,
                    name=t.name,
                    bars=[
                        TrackBarRef(
                            bar_index=tb.bar_index,
                            clip=clip_map[tb.clip_id]
                        )
                        for tb in our_tbars
                    ]
                )
            )

        # 7. Assemble composition
        return Composition(
            id=composition_id,
            ticks_per_quarter=comp.ticks_per_quarter,
            tempo_bpm=comp.tempo_bpm,
            tracks=track_objs
        )

    async def _load_clips(self, clip_ids):
        """
        Load Clip → ClipBars → Notes and attach all MIDI expression curves.
        Returns a dict: clip_id → Clip object
        """
        # Load data from DB
        clips = await self.clip_repo.get_clips(clip_ids)
        clip_bars = await self.clip_bar_repo.get_bars_by_clips(clip_ids)
        notes = await self.note_repo.get_notes_by_clips(clip_ids)

        # Group notes by clip_bar_id
        notes_by_bar = {}
        for n in notes:
            notes_by_bar.setdefault(n.clip_bar_id, []).append(
                Note(
                    start_unit=n.start_unit,
                    duration_units=n.duration_units,
                    midi_pitch=n.midi_pitch,
                    velocity=n.velocity,
                    is_rest=n.is_rest,
                    articulation=n.articulation,
                    expression=n.expression,
                    microtiming_offset=n.microtiming_offset,
                    metadata=n.metadata
                )
            )

        # Group ClipBars by clip_id
        bars_by_clip = {}
        for b in clip_bars:
            bars_by_clip.setdefault(b.clip_id, []).append(
                Bar(
                    notes=notes_by_bar.get(b.id, []),
                    velocity_curve=b.velocity_curve,
                    cc=b.cc,
                    pitch_bend_curve=b.pitch_bend_curve,
                    aftertouch_curve=b.aftertouch_curve,
                    pedal_events=b.pedal_events,
                    metadata=b.metadata
                )
            )

        # Build final Clip objects
        clip_map = {
            c.id: Clip(
                id=c.id,
                bars=bars_by_clip.get(c.id, [])
            )
            for c in clips
        }

        return clip_map

