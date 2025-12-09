# clip_service.py
# Async business logic for clip operations

from typing import List, Dict, Any, Optional
from src.repository import (
    get_database,
    ClipRepository,
    ClipBarRepository,
    NoteRepository
)
from src.core import Clip as ClipModel


class ClipService:
    """
    Async service layer for clip operations.
    Orchestrates multiple repository calls and implements business logic.
    """
    
    def __init__(self, database=None):
        """
        Initialize service with repositories.
        
        Args:
            database: Database instance (uses singleton if None)
        """
        self.db = database or get_database()
        self.clip_repo = ClipRepository()
        self.clip_bar_repo = ClipBarRepository()
        self.note_repo = NoteRepository()
    
    async def create_clip_from_dsl(self, dsl_clip: Dict[str, Any]) -> int:
        """
        Create a complete clip from DSL format.
        
        This orchestrates:
        1. Insert clip record
        2. Insert clip_bars for each bar
        3. Insert notes for each bar
        
        Args:
            dsl_clip: Clip data in DSL format with structure:
                {
                    "id": int (optional),
                    "name": str,
                    "track_name": str (optional),
                    "bars": [
                        {
                            "clip_id": int,
                            "bar_index": int,
                            "notes": [
                                {
                                    "absolute_pitch": int,
                                    "start": float,
                                    "duration": float,
                                    "is_rest": bool,
                                    ...
                                }
                            ],
                            "velocity_curve": [...] (optional),
                            "cc": {...} (optional),
                            ...
                        }
                    ]
                }
        
        Returns:
            ID of created clip
        """
        async with self.db.session() as session:
            # 1. Insert clip
            clip_data = {
                "name": dsl_clip["name"],
                "track_name": dsl_clip.get("track_name")
            }
            clip_id = await self.clip_repo.insert(session, clip_data)
            
            # 2. Insert clip bars and notes
            for bar_data in dsl_clip.get("bars", []):
                # Insert clip bar with expression curves
                clip_bar_data = {
                    "clip_id": clip_id,
                    "bar_index": bar_data["bar_index"],
                    "velocity_curve": bar_data.get("velocity_curve"),
                    "cc": bar_data.get("cc"),
                    "pitch_bend_curve": bar_data.get("pitch_bend_curve"),
                    "aftertouch_curve": bar_data.get("aftertouch_curve"),
                    "pedal_events": bar_data.get("pedal_events"),
                    "metadata": bar_data.get("metadata")
                }
                clip_bar_id = await self.clip_bar_repo.insert(session, clip_bar_data)
                
                # 3. Insert notes for this bar
                for note_data in bar_data.get("notes", []):
                    note_insert = {
                        "clip_bar_id": clip_bar_id,
                        "pitch": note_data.get("absolute_pitch"),
                        "start_beat": note_data.get("start"),
                        "duration_beats": note_data.get("duration"),
                        "is_rest": note_data.get("is_rest", False),
                        "scale_degree": note_data.get("scale_degree"),
                        "interval_from_prev": note_data.get("interval_from_prev"),
                        "cents_offset": note_data.get("cents_offset"),
                        "articulation": note_data.get("articulation"),
                        "dynamics": note_data.get("dynamics"),
                        "expression": note_data.get("expression")
                    }
                    await self.note_repo.insert(session, note_insert)
            
            return clip_id
    
    async def get_clip_with_bars_and_notes(self, clip_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a complete clip with all its bars and notes.
        
        Args:
            clip_id: ID of the clip
        
        Returns:
            Dictionary with clip, bars, and notes, or None if not found
        """
        async with self.db.session() as session:
            # Get clip
            clip = await self.clip_repo.get_by_id(session, clip_id)
            if not clip:
                return None
            
            # Get bars
            bars = await self.clip_bar_repo.find_by_clip_id(session, clip_id)
            
            # Get notes for each bar
            for bar in bars:
                bar["notes"] = await self.note_repo.find_by_clip_bar_id(session, bar["id"])
            
            clip["bars"] = bars
            return clip
    
    async def find_clips_by_tag(self, tag: str) -> List[ClipModel]:
        """
        Find clips by metadata tag.
        
        Searches for clips that have bars with metadata containing the specified tag.
        
        Args:
            tag: Tag to search for
        
        Returns:
            List of Pydantic Clip objects
        """
        async with self.db.session() as session:
            # Find all clip bars with metadata containing the tag
            from sqlalchemy import select
            from src.core.schema import clip_bars, clips
            
            stmt = (
                select(clips.c.id)
                .select_from(
                    clips.join(clip_bars, clips.c.id == clip_bars.c.clip_id)
                )
                .where(
                    clip_bars.c.metadata.isnot(None)
                )
                .distinct()
            )
            
            result = await session.execute(stmt)
            results = result.fetchall()
            clip_ids = [row[0] for row in results]
            
            # Filter by tag in metadata (JSON field)
            matching_clips = []
            for clip_id in clip_ids:
                clip_data = await self.get_clip_with_bars_and_notes(clip_id)
                if clip_data:
                    # Check if any bar has the tag in metadata
                    for bar in clip_data.get("bars", []):
                        metadata = bar.get("metadata", {})
                        if metadata and tag in str(metadata.get("tag", "")):
                            matching_clips.append(self._dict_to_clip_model(clip_data))
                            break
            
            return matching_clips
    
    async def find_clips_by_name(self, name_pattern: str) -> List[Dict[str, Any]]:
        """
        Search clips by name pattern.
        
        Args:
            name_pattern: Pattern to search for (e.g., "%lead%")
        
        Returns:
            List of clip dictionaries
        """
        async with self.db.session() as session:
            return await self.clip_repo.search_by_name(session, name_pattern)
    
    async def delete_clip(self, clip_id: int) -> bool:
        """
        Delete a clip and all its associated bars and notes.
        
        Args:
            clip_id: ID of the clip to delete
        
        Returns:
            True if deleted, False if not found
        """
        async with self.db.session() as session:
            # Cascade delete will handle bars and notes
            return await self.clip_repo.delete_by_id(session, clip_id)
    
    def _dict_to_clip_model(self, clip_dict: Dict[str, Any]) -> ClipModel:
        """
        Convert a clip dictionary to a Pydantic Clip model.
        
        Args:
            clip_dict: Clip dictionary with bars and notes
        
        Returns:
            Pydantic Clip object
        """
        from src.core import ClipBar as ClipBarModel
        
        bars = []
        for bar_dict in clip_dict.get("bars", []):
            bar_model = ClipBarModel(
                id=bar_dict.get("id"),
                clip_id=bar_dict["clip_id"],
                bar_index=bar_dict["bar_index"],
                velocity_curve=bar_dict.get("velocity_curve"),
                cc=bar_dict.get("cc"),
                pitch_bend_curve=bar_dict.get("pitch_bend_curve"),
                aftertouch_curve=bar_dict.get("aftertouch_curve"),
                pedal_events=bar_dict.get("pedal_events"),
                metadata=bar_dict.get("metadata")
            )
            bars.append(bar_model)
        
        return ClipModel(
            id=clip_dict.get("id"),
            name=clip_dict["name"],
            track_name=clip_dict.get("track_name"),
            bars=bars
        )
