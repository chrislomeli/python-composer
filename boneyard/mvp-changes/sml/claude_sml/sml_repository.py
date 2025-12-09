from sqlalchemy import create_engine, insert, select, and_, or_
from sqlalchemy.engine import Engine
from typing import Dict, Any, List, Optional
import json
from sml_models import metadata, Clip, clip_tags, notes,clips, ProjectContainer, tempo_map, clip_instances, projects, loops, meter_map,key_map, tracks,bar_overrides

# Import from the models file
# from music_dsl_models import (
#     metadata, projects, tempo_map, meter_map, key_map,
#     tracks, clip_instances, bar_overrides, loops, clips, notes, clip_tags,
#     ProjectContainer, Clip
# )


class MusicDSLRepository:
    """Repository for inserting and querying music DSL data using SQLAlchemy Core."""

    def __init__(self, engine: Engine):
        self.engine = engine

    def create_tables(self):
        """Create all tables in the database."""
        metadata.create_all(self.engine)

    # ========================================================================
    # CLIP OPERATIONS (Independent of Projects)
    # ========================================================================

    def insert_clip(self, clip_data: Dict[str, Any]) -> int:
        """
        Insert a clip into the library.
        Returns the database ID of the clip.
        """
        clip = Clip(**clip_data)

        with self.engine.begin() as conn:
            # Insert clip
            result = conn.execute(
                insert(clips).values(
                    clip_id=clip.clip_id,
                    name=clip.name,
                    style=clip.style
                )
            )
            db_clip_id = result.inserted_primary_key[0]

            # Insert tags if present
            if clip.tags:
                tag_values = [
                    {'clip_id': db_clip_id, 'tag': tag}
                    for tag in clip.tags
                ]
                conn.execute(insert(clip_tags).values(tag_values))

            # Insert notes
            if clip.notes:
                note_values = [
                    {
                        'clip_id': db_clip_id,
                        'pitch': note.pitch,
                        'start_beat': note.start_beat,
                        'duration_beats': note.duration_beats,
                        'is_rest': note.is_rest or False
                    }
                    for note in clip.notes
                ]
                conn.execute(insert(notes).values(note_values))

            return db_clip_id

    def insert_clips_batch(self, clips_data: List[Dict[str, Any]]) -> List[int]:
        """Insert multiple clips at once. Returns list of database IDs."""
        return [self.insert_clip(clip) for clip in clips_data]

    def get_clip_by_clip_id(self, clip_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a clip by its user-facing clip_id."""
        with self.engine.connect() as conn:
            clip_row = conn.execute(
                select(clips).where(clips.c.clip_id == clip_id)
            ).fetchone()

            if not clip_row:
                return None

            # Get tags
            tag_rows = conn.execute(
                select(clip_tags.c.tag).where(clip_tags.c.clip_id == clip_row.id)
            ).fetchall()

            # Get notes
            note_rows = conn.execute(
                select(notes).where(notes.c.clip_id == clip_row.id)
            ).fetchall()

            return {
                'clip_id': clip_row.clip_id,
                'name': clip_row.name,
                'style': clip_row.style,
                'tags': [t.tag for t in tag_rows] if tag_rows else None,
                'notes': [
                    {
                        'pitch': n.pitch,
                        'start_beat': n.start_beat,
                        'duration_beats': n.duration_beats,
                        'is_rest': n.is_rest
                    }
                    for n in note_rows
                ]
            }

    def search_clips_by_tags(self, tags: List[str], match_all: bool = False) -> List[Dict[str, Any]]:
        """
        Search for clips by tags.

        Args:
            tags: List of tags to search for
            match_all: If True, clip must have ALL tags. If False, clip must have ANY tag.

        Returns:
            List of clip dictionaries
        """
        with self.engine.connect() as conn:
            if match_all:
                # Clip must have all tags - use HAVING COUNT
                subquery = (
                    select(clip_tags.c.clip_id)
                    .where(clip_tags.c.tag.in_(tags))
                    .group_by(clip_tags.c.clip_id)
                    .having(func.count(clip_tags.c.tag.distinct()) == len(tags))
                )
                clip_ids = [row.clip_id for row in conn.execute(subquery).fetchall()]
            else:
                # Clip must have any tag
                tag_rows = conn.execute(
                    select(clip_tags.c.clip_id.distinct())
                    .where(clip_tags.c.tag.in_(tags))
                ).fetchall()
                clip_ids = [row.clip_id for row in tag_rows]

            if not clip_ids:
                return []

            # Get full clip data for matching clips
            results = []
            for clip_id in clip_ids:
                clip_row = conn.execute(
                    select(clips).where(clips.c.id == clip_id)
                ).fetchone()

                if clip_row:
                    results.append(self.get_clip_by_clip_id(clip_row.clip_id))

            return results

    def search_clips_by_style(self, style: str) -> List[Dict[str, Any]]:
        """Search for clips by style."""
        with self.engine.connect() as conn:
            clip_rows = conn.execute(
                select(clips).where(clips.c.style == style)
            ).fetchall()

            return [self.get_clip_by_clip_id(row.clip_id) for row in clip_rows]

    def list_all_clips(self) -> List[Dict[str, Any]]:
        """Get all clips in the library."""
        with self.engine.connect() as conn:
            clip_rows = conn.execute(select(clips)).fetchall()
            return [self.get_clip_by_clip_id(row.clip_id) for row in clip_rows]

    # ========================================================================
    # PROJECT OPERATIONS
    # ========================================================================

    def insert_project(self, project_data: Dict[str, Any]) -> int:
        """
        Insert a project. Assumes all referenced clips already exist in the library.
        Returns the project_id.
        """
        # Validate with Pydantic
        container = ProjectContainer(**project_data)
        proj = container.project

        with self.engine.begin() as conn:
            # 1. Insert project
            result = conn.execute(
                insert(projects).values(
                    name=proj.name,
                    ticks_per_quarter=proj.ticks_per_quarter
                )
            )
            project_id = result.inserted_primary_key[0]

            # 2. Insert tempo map
            if proj.tempo_map:
                tempo_values = [
                    {
                        'project_id': project_id,
                        'bar': entry.bar,
                        'tempo_bpm': entry.tempo_bpm
                    }
                    for entry in proj.tempo_map
                ]
                conn.execute(insert(tempo_map).values(tempo_values))

            # 3. Insert meter map
            if proj.meter_map:
                meter_values = [
                    {
                        'project_id': project_id,
                        'bar': entry.bar,
                        'numerator': entry.numerator,
                        'denominator': entry.denominator
                    }
                    for entry in proj.meter_map
                ]
                conn.execute(insert(meter_map).values(meter_values))

            # 4. Insert key map
            if proj.key_map:
                key_values = [
                    {
                        'project_id': project_id,
                        'bar': entry.bar,
                        'key': entry.key,
                        'mode': entry.mode
                    }
                    for entry in proj.key_map
                ]
                conn.execute(insert(key_map).values(key_values))

            # 5. Verify all referenced clips exist
            referenced_clip_ids = set()
            for track_data in proj.tracks.values():
                for clip_inst in track_data.clips:
                    referenced_clip_ids.add(clip_inst.clip_id)

            for clip_id in referenced_clip_ids:
                exists = conn.execute(
                    select(clips.c.id).where(clips.c.clip_id == clip_id)
                ).fetchone()
                if not exists:
                    raise ValueError(f"Referenced clip_id {clip_id} does not exist in clip library")

            # 6. Insert tracks and their clip instances
            for track_name, track_data in proj.tracks.items():
                track_result = conn.execute(
                    insert(tracks).values(
                        project_id=project_id,
                        track_name=track_name,
                        instrument_name=track_data.instrument.name,
                        midi_channel=track_data.instrument.midi_channel
                    )
                )
                track_id = track_result.inserted_primary_key[0]

                # Insert clip instances for this track
                for clip_inst in track_data.clips:
                    clip_inst_result = conn.execute(
                        insert(clip_instances).values(
                            track_id=track_id,
                            clip_instance_id=clip_inst.clip_instance_id,
                            clip_id=clip_inst.clip_id,  # Store user-facing clip_id directly
                            start_bar=clip_inst.start_bar,
                            length_bars=clip_inst.length_bars
                        )
                    )
                    clip_inst_db_id = clip_inst_result.inserted_primary_key[0]

                    # Insert bar overrides if present
                    if clip_inst.bar_overrides:
                        for override in clip_inst.bar_overrides:
                            # Convert Pydantic models to JSON-serializable dicts
                            velocity_curve_json = (
                                [p.model_dump() for p in override.velocity_curve]
                                if override.velocity_curve else None
                            )

                            cc_lanes_json = None
                            if override.cc_lanes:
                                cc_lanes_json = {
                                    k: [p.model_dump() for p in v]
                                    for k, v in override.cc_lanes.items()
                                }

                            pitch_bend_json = (
                                [p.model_dump() for p in override.pitch_bend_curve]
                                if override.pitch_bend_curve else None
                            )

                            aftertouch_json = (
                                [p.model_dump() for p in override.aftertouch_curve]
                                if override.aftertouch_curve else None
                            )

                            conn.execute(
                                insert(bar_overrides).values(
                                    clip_instance_id=clip_inst_db_id,
                                    bar_index=override.bar_index,
                                    velocity_curve=velocity_curve_json,
                                    cc_lanes=cc_lanes_json,
                                    pitch_bend_curve=pitch_bend_json,
                                    aftertouch_curve=aftertouch_json,
                                    pedal_events=override.pedal_events,
                                    metadata=override.metadata
                                )
                            )

            # 7. Insert loops
            if proj.loops:
                loop_values = [
                    {
                        'project_id': project_id,
                        'start_bar': loop.start_bar,
                        'length_bars': loop.length_bars,
                        'repeat_count': loop.repeat_count
                    }
                    for loop in proj.loops
                ]
                conn.execute(insert(loops).values(loop_values))

            return project_id

    def get_project_by_name(self, name: str) -> Dict[str, Any]:
        """Retrieve a project by name and return it in DSL format."""
        with self.engine.connect() as conn:
            # Get project
            proj_result = conn.execute(
                select(projects).where(projects.c.name == name)
            ).fetchone()

            if not proj_result:
                raise ValueError(f"Project '{name}' not found")

            project_id = proj_result.id

            # Get tempo map
            tempo_results = conn.execute(
                select(tempo_map).where(tempo_map.c.project_id == project_id)
            ).fetchall()

            # Get meter map
            meter_results = conn.execute(
                select(meter_map).where(meter_map.c.project_id == project_id)
            ).fetchall()

            # Get key map
            key_results = conn.execute(
                select(key_map).where(key_map.c.project_id == project_id)
            ).fetchall()

            # Get loops
            loop_results = conn.execute(
                select(loops).where(loops.c.project_id == project_id)
            ).fetchall()

            # Get tracks
            track_results = conn.execute(
                select(tracks).where(tracks.c.project_id == project_id)
            ).fetchall()

            tracks_dict = {}
            for track_row in track_results:
                # Get clip instances for this track
                clip_inst_results = conn.execute(
                    select(clip_instances).where(
                        clip_instances.c.track_id == track_row.id
                    )
                ).fetchall()

                clips_list = []
                for ci_row in clip_inst_results:
                    # Get bar overrides
                    override_results = conn.execute(
                        select(bar_overrides).where(
                            bar_overrides.c.clip_instance_id == ci_row.id
                        )
                    ).fetchall()

                    bar_overrides_list = [
                        {
                            'bar_index': bo.bar_index,
                            'velocity_curve': bo.velocity_curve,
                            'cc_lanes': bo.cc_lanes,
                            'pitch_bend_curve': bo.pitch_bend_curve,
                            'aftertouch_curve': bo.aftertouch_curve,
                            'pedal_events': bo.pedal_events,
                            'metadata': bo.metadata
                        }
                        for bo in override_results
                    ] if override_results else None

                    clips_list.append({
                        'clip_instance_id': ci_row.clip_instance_id,
                        'clip_id': ci_row.clip_id,  # This is the user-facing clip_id
                        'start_bar': ci_row.start_bar,
                        'length_bars': ci_row.length_bars,
                        'bar_overrides': bar_overrides_list
                    })

                tracks_dict[track_row.track_name] = {
                    'instrument': {
                        'name': track_row.instrument_name,
                        'midi_channel': track_row.midi_channel
                    },
                    'clips': clips_list
                }

            return {
                'project': {
                    'name': proj_result.name,
                    'ticks_per_quarter': proj_result.ticks_per_quarter,
                    'tempo_map': [
                        {'bar': t.bar, 'tempo_bpm': t.tempo_bpm}
                        for t in tempo_results
                    ],
                    'meter_map': [
                        {'bar': m.bar, 'numerator': m.numerator, 'denominator': m.denominator}
                        for m in meter_results
                    ],
                    'key_map': [
                        {'bar': k.bar, 'key': k.key, 'mode': k.mode}
                        for k in key_results
                    ],
                    'tracks': tracks_dict,
                    'loops': [
                        {'start_bar': l.start_bar, 'length_bars': l.length_bars, 'repeat_count': l.repeat_count}
                        for l in loop_results
                    ] if loop_results else None
                }
            }


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == '__main__':
    from sqlalchemy import func

    # Create an in-memory SQLite database for testing
    engine = create_engine('sqlite:///:memory:', echo=True)

    repo = MusicDSLRepository(engine)
    repo.create_tables()

    print("=" * 80)
    print("STEP 1: Create clips in the library")
    print("=" * 80)

    # First, create some clips
    clip1 = {
        "clip_id": 8,
        "name": "lead-riff-intro",
        "style": "latin",
        "tags": ["intro", "lead", "energetic"],
        "notes": [
            {"pitch": 60, "start_beat": 0.0, "duration_beats": 1.0},
            {"pitch": 64, "start_beat": 1.0, "duration_beats": 1.0},
            {"pitch": 67, "start_beat": 2.0, "duration_beats": 1.0},
            {"is_rest": True, "start_beat": 3.0, "duration_beats": 1.0}
        ]
    }

    clip2 = {
        "clip_id": 9,
        "name": "lead-riff-bridge",
        "style": "latin",
        "tags": ["bridge", "lead", "mellow"],
        "notes": [
            {"pitch": 60, "start_beat": 0.0, "duration_beats": 1.0},
            {"pitch": 60, "start_beat": 1.0, "duration_beats": 1.0},
            {"pitch": 60, "start_beat": 2.0, "duration_beats": 1.0},
            {"is_rest": True, "start_beat": 3.0, "duration_beats": 1.0}
        ]
    }

    clip3 = {
        "clip_id": 10,
        "name": "bass-riff",
        "style": "latin",
        "tags": ["bass", "groove", "intro"],
        "notes": [
            {"pitch": 48, "start_beat": 0.0, "duration_beats": 1.0},
            {"pitch": 46, "start_beat": 1.0, "duration_beats": 1.0},
            {"pitch": 72, "start_beat": 2.0, "duration_beats": 1.0},
            {"is_rest": True, "start_beat": 3.0, "duration_beats": 1.0}
        ]
    }

    repo.insert_clip(clip1)
    repo.insert_clip(clip2)
    repo.insert_clip(clip3)

    print("\n" + "=" * 80)
    print("STEP 2: Search clips by tags")
    print("=" * 80)

    # Search for clips with "intro" tag
    intro_clips = repo.search_clips_by_tags(["intro"])
    print(f"\nFound {len(intro_clips)} clips with 'intro' tag:")
    for clip in intro_clips:
        print(f"  - {clip['name']} (clip_id: {clip['clip_id']})")

    # Search for clips with "lead" tag
    lead_clips = repo.search_clips_by_tags(["lead"])
    print(f"\nFound {len(lead_clips)} clips with 'lead' tag:")
    for clip in lead_clips:
        print(f"  - {clip['name']} (clip_id: {clip['clip_id']})")

    print("\n" + "=" * 80)
    print("STEP 3: Create a project using existing clips")
    print("=" * 80)

    # Now create a project that references these clips
    project_data = {
        "project": {
            "name": "phrase_loop_example",
            "ticks_per_quarter": 480,
            "tempo_map": [
                {"bar": 1, "tempo_bpm": 120}
            ],
            "meter_map": [
                {"bar": 1, "numerator": 4, "denominator": 4}
            ],
            "key_map": [
                {"bar": 1, "key": "C", "mode": "major"}
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
                            "clip_id": 8,  # References clip from library
                            "start_bar": 1,
                            "length_bars": 2,
                            "bar_overrides": [
                                {
                                    "bar_index": 1,
                                    "velocity_curve": [
                                        {"time": 0, "value": 90},
                                        {"time": 4, "value": 100}
                                    ],
                                    "cc_lanes": {
                                        "1": [
                                            {"time": 0, "value": 64}
                                        ]
                                    },
                                    "pitch_bend_curve": [
                                        {"time": 0, "value": 0},
                                        {"time": 4, "value": 200}
                                    ],
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
                            "clip_id": 10,  # References clip from library
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
            ]
        }
    }

    project_id = repo.insert_project(project_data)
    print(f"\nCreated project with ID: {project_id}")

    print("\n" + "=" * 80)
    print("STEP 4: Retrieve the project")
    print("=" * 80)

    # Retrieve it back
    retrieved = repo.get_project_by_name("phrase_loop_example")
    print("\nRetrieved project:")
    print(json.dumps(retrieved, indent=2))

    print("\n" + "=" * 80)
    print("STEP 5: Get full clip details for a clip used in the project")
    print("=" * 80)

    # Get the full clip details
    full_clip = repo.get_clip_by_clip_id(8)
    print("\nFull clip details for clip_id 8:")
    print(json.dumps(full_clip, indent=2))