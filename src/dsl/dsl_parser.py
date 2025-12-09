# dsl_parser.py
# Parser to convert DSL JSON (from DSL.md) to spec-compliant AST models
# Maps the project DSL structure to Pydantic models matching spec §2.1-2.5

from typing import Dict, List, Any, Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dsl.sml_ast import (
    Clip, ClipBar, Track, TrackBarRef, Composition,
    BarExpressionModel
)


class DSLParser:
    """
    Parses DSL JSON format (as defined in DSL.md) into spec-compliant AST models.
    
    DSL Structure:
    {
      "project": {
        "name": "...",
        "ticks_per_quarter": 480,
        "tempo_map": [...],
        "meter_map": [...],
        "key_map": [...],
        "tracks": {
          "track_name": {
            "instrument": {...},
            "clips": [...]
          }
        },
        "loops": [...],
        "clip_library": [...]
      }
    }
    """
    
    def __init__(self):
        self.clip_library: Dict[int, Clip] = {}
    
    def parse_project(self, dsl_json: Dict[str, Any]) -> Composition:
        """
        Parse a complete DSL project into a Composition AST.
        
        Args:
            dsl_json: DSL JSON with "project" key
            
        Returns:
            Composition AST object
        """
        if "project" not in dsl_json:
            raise ValueError("DSL JSON must have 'project' key")
        
        project = dsl_json["project"]
        
        # Parse clip library first (clips are referenced by tracks)
        if "clip_library" in project:
            self._parse_clip_library(project["clip_library"])
        
        # Parse tracks
        tracks = []
        if "tracks" in project:
            for track_name, track_data in project["tracks"].items():
                track = self._parse_track(track_name, track_data)
                tracks.append(track)
        
        # Create composition
        composition = Composition(
            name=project.get("name", "Untitled"),
            ticks_per_quarter=project.get("ticks_per_quarter", 480),
            tempo_bpm=self._get_initial_tempo(project.get("tempo_map", [])),
            tracks=tracks,
            tempo_map=project.get("tempo_map"),
            meter_map=project.get("meter_map"),
            key_map=project.get("key_map"),
            loops=project.get("loops")
        )
        
        return composition
    
    def _parse_clip_library(self, clip_library: List[Dict[str, Any]]) -> None:
        """
        Parse clip library and store clips by clip_id.
        
        DSL Clip format:
        {
          "clip_id": 8,
          "name": "lead-riff-intro",
          "style": "latin",
          "notes": [
            {"pitch": 60, "start_beat": 0.0, "duration_beats": 1.0},
            {"is_rest": true, "start_beat": 3.0, "duration_beats": 1.0}
          ]
        }
        """
        for clip_data in clip_library:
            clip_id = clip_data.get("clip_id")
            if clip_id is None:
                raise ValueError("Clip must have 'clip_id'")
            
            # Convert notes to ClipBars
            # Group notes by bar (assuming 4 beats per bar for now)
            bars = self._notes_to_clipbars(
                clip_id=clip_id,
                notes=clip_data.get("notes", []),
                beats_per_bar=4.0
            )
            
            clip = Clip(
                clip_id=clip_id,
                name=clip_data.get("name"),
                track_name=None,  # Will be set when used in track
                bars=bars
            )
            
            self.clip_library[clip_id] = clip
    
    def _notes_to_clipbars(
        self, 
        clip_id: int, 
        notes: List[Dict[str, Any]], 
        beats_per_bar: float = 4.0
    ) -> List[ClipBar]:
        """
        Convert a flat list of notes into ClipBar objects grouped by bar.
        
        Args:
            clip_id: ID of the clip
            notes: List of note dicts with start_beat, duration_beats, pitch
            beats_per_bar: Beats per bar (default 4.0 for 4/4 time)
            
        Returns:
            List of ClipBar objects
        """
        # Group notes by bar
        bars_dict: Dict[int, List[Dict[str, Any]]] = {}
        
        for note in notes:
            start_beat = note.get("start_beat", 0.0)
            bar_index = int(start_beat // beats_per_bar)
            
            if bar_index not in bars_dict:
                bars_dict[bar_index] = []
            
            # Adjust start_beat to be relative to bar
            note_copy = note.copy()
            note_copy["start"] = start_beat % beats_per_bar
            note_copy["duration"] = note.get("duration_beats", 1.0)
            note_copy["absolute_pitch"] = note.get("pitch", 0)
            
            bars_dict[bar_index].append(note_copy)
        
        # Create ClipBar objects
        clip_bars = []
        for bar_index in sorted(bars_dict.keys()):
            clip_bar = ClipBar(
                bar_index=bar_index,
                items=[],  # We'll store notes directly in the output
                expression=None
            )
            # Store notes for later conversion
            clip_bar._notes = bars_dict[bar_index]  # Temporary storage
            clip_bars.append(clip_bar)
        
        return clip_bars
    
    def _parse_track(self, track_name: str, track_data: Dict[str, Any]) -> Track:
        """
        Parse a track from DSL format.
        
        DSL Track format:
        {
          "instrument": {
            "name": "lead-kazoo",
            "midi_channel": 0
          },
          "clips": [
            {
              "clip_instance_id": "lead_1",
              "clip_id": 8,
              "start_bar": 1,
              "length_bars": 2,
              "bar_overrides": [...]
            }
          ]
        }
        """
        clips = track_data.get("clips", [])
        track_bars: List[TrackBarRef] = []
        
        # Process each clip instance
        for clip_instance in clips:
            clip_id = clip_instance.get("clip_id")
            start_bar = clip_instance.get("start_bar", 1)
            length_bars = clip_instance.get("length_bars", 1)
            bar_overrides = clip_instance.get("bar_overrides", [])
            
            # Get clip from library
            if clip_id not in self.clip_library:
                raise ValueError(f"Clip {clip_id} not found in clip_library")
            
            clip = self.clip_library[clip_id]
            
            # Apply bar overrides to clip bars
            if bar_overrides:
                self._apply_bar_overrides(clip, bar_overrides)
            
            # Create TrackBarRef entries for each bar in the clip instance
            for i in range(length_bars):
                track_bar_index = start_bar + i
                clip_bar_index = i % len(clip.bars) if clip.bars else 0
                
                track_bar_ref = TrackBarRef(
                    bar_index=track_bar_index,
                    clip_id=clip_id,
                    clip_bar_index=clip_bar_index
                )
                track_bars.append(track_bar_ref)
        
        track = Track(
            name=track_name,
            bars=track_bars
        )
        
        return track
    
    def _apply_bar_overrides(
        self, 
        clip: Clip, 
        bar_overrides: List[Dict[str, Any]]
    ) -> None:
        """
        Apply bar-level expression overrides to clip bars.
        
        DSL bar_override format:
        {
          "bar_index": 1,
          "velocity_curve": [{"time": 0, "value": 90}, {"time": 4, "value": 100}],
          "cc_lanes": {"1": [{"time": 0, "value": 64}]},
          "pitch_bend_curve": [{"time": 0, "value": 0}],
          "aftertouch_curve": null,
          "pedal_events": null,
          "metadata": {"tag": "intro"}
        }
        """
        for override in bar_overrides:
            bar_index = override.get("bar_index")
            
            # Find the clip bar to override
            clip_bar = None
            for cb in clip.bars:
                if cb.bar_index == bar_index:
                    clip_bar = cb
                    break
            
            if clip_bar is None:
                continue
            
            # Convert cc_lanes from string keys to int keys
            cc = None
            if "cc_lanes" in override and override["cc_lanes"]:
                cc = {int(k): v for k, v in override["cc_lanes"].items()}
            
            # Create bar expression model
            bar_expr = BarExpressionModel(
                velocity_curve=override.get("velocity_curve"),
                cc=cc,
                pitch_bend_curve=override.get("pitch_bend_curve"),
                aftertouch_curve=override.get("aftertouch_curve"),
                pedal_events=override.get("pedal_events"),
                metadata=override.get("metadata")
            )
            
            clip_bar.expression = bar_expr
    
    def _get_initial_tempo(self, tempo_map: List[Dict[str, Any]]) -> int:
        """Get the initial tempo from tempo_map, or default to 120."""
        if tempo_map and len(tempo_map) > 0:
            return int(tempo_map[0].get("tempo_bpm", 120))
        return 120
    
    def to_database_format(self, composition: Composition) -> Dict[str, Any]:
        """
        Convert Composition AST to database-ready format.
        
        Returns a dict with:
        - composition: Composition data
        - clips: List of clips with bars and notes
        - tracks: List of tracks with bar references
        """
        # Collect all unique clips
        clips_data = []
        for clip_id, clip in self.clip_library.items():
            clip_dict = {
                "id": clip.clip_id,
                "name": clip.name,
                "track_name": clip.track_name,
                "bars": []
            }
            
            for clip_bar in clip.bars:
                bar_dict = {
                    "clip_id": clip.clip_id,
                    "bar_index": clip_bar.bar_index,
                    "notes": getattr(clip_bar, "_notes", [])
                }
                
                # Add expression curves if present
                if clip_bar.expression:
                    expr = clip_bar.expression.model_dump(exclude_none=True)
                    bar_dict.update(expr)
                
                clip_dict["bars"].append(bar_dict)
            
            clips_data.append(clip_dict)
        
        # Convert tracks
        tracks_data = []
        for track in composition.tracks:
            track_dict = {
                "name": track.name,
                "bars": [bar.model_dump() for bar in track.bars]
            }
            tracks_data.append(track_dict)
        
        return {
            "composition": {
                "name": composition.name,
                "ticks_per_quarter": composition.ticks_per_quarter,
                "tempo_bpm": composition.tempo_bpm
            },
            "clips": clips_data,
            "tracks": tracks_data
        }


# Convenience functions
def parse_dsl_file(filepath: str) -> Composition:
    """Parse a DSL JSON file into a Composition AST."""
    import json
    with open(filepath, 'r') as f:
        dsl_json = json.load(f)
    
    parser = DSLParser()
    return parser.parse_project(dsl_json)


def parse_dsl_string(dsl_string: str) -> Composition:
    """Parse a DSL JSON string into a Composition AST."""
    import json
    dsl_json = json.loads(dsl_string)
    
    parser = DSLParser()
    return parser.parse_project(dsl_json)


# Example usage
if __name__ == "__main__":
    # Example DSL JSON (from DSL.md)
    example_dsl = {
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
                            "clip_id": 8,
                            "start_bar": 1,
                            "length_bars": 2,
                            "bar_overrides": [
                                {
                                    "bar_index": 0,
                                    "velocity_curve": [
                                        {"time": 0, "value": 90},
                                        {"time": 4, "value": 100}
                                    ],
                                    "cc_lanes": {
                                        "1": [{"time": 0, "value": 64}]
                                    }
                                }
                            ]
                        }
                    ]
                }
            },
            "clip_library": [
                {
                    "clip_id": 8,
                    "name": "lead-riff-intro",
                    "style": "latin",
                    "notes": [
                        {"pitch": 60, "start_beat": 0.0, "duration_beats": 1.0},
                        {"pitch": 64, "start_beat": 1.0, "duration_beats": 1.0},
                        {"pitch": 67, "start_beat": 2.0, "duration_beats": 1.0},
                        {"is_rest": True, "start_beat": 3.0, "duration_beats": 1.0}
                    ]
                }
            ]
        }
    }
    
    try:
        parser = DSLParser()
        composition = parser.parse_project(example_dsl)
        
        print("✓ Parsed DSL successfully")
        print(f"Composition: {composition.name}")
        print(f"Tracks: {len(composition.tracks)}")
        print(f"Clips in library: {len(parser.clip_library)}")
        
        # Convert to database format
        db_format = parser.to_database_format(composition)
        print("\n✓ Converted to database format")
        
        import json
        print(json.dumps(db_format, indent=2))
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
