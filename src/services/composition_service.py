# composition_service.py
# Async business logic for composition operations

from typing import List, Dict, Any, Optional
from src.repository import (
    get_database,
    CompositionRepository,
    TrackRepository,
    TrackBarRepository
)
from src.core import Composition as CompositionModel


class CompositionService:
    """
    Async service layer for composition operations.
    Orchestrates multiple repository calls and implements business logic.
    """
    
    def __init__(self, database=None):
        """
        Initialize service with repositories.
        
        Args:
            database: Database instance (uses singleton if None)
        """
        self.db = database or get_database()
        self.composition_repo = CompositionRepository()
        self.track_repo = TrackRepository()
        self.track_bar_repo = TrackBarRepository()
    
    async def create_composition_from_dsl(self, dsl_composition: Dict[str, Any]) -> int:
        """
        Create a complete composition from DSL format.
        
        This orchestrates:
        1. Insert composition record
        2. Insert tracks
        3. Insert track_bars for each track
        
        Args:
            dsl_composition: Composition data in DSL format with structure:
                {
                    "name": str,
                    "ticks_per_quarter": int,
                    "tempo_bpm": int,
                    "tracks": [
                        {
                            "name": str,
                            "bars": [
                                {
                                    "bar_index": int,
                                    "clip_id": int,
                                    "clip_bar_index": int
                                }
                            ]
                        }
                    ]
                }
        
        Returns:
            ID of created composition
        """
        async with self.db.session() as session:
            # 1. Insert composition
            comp_data = {
                "name": dsl_composition["name"],
                "ticks_per_quarter": dsl_composition.get("ticks_per_quarter", 480),
                "tempo_bpm": dsl_composition.get("tempo_bpm", 120)
            }
            composition_id = await self.composition_repo.insert(session, comp_data)
            
            # 2. Insert tracks and track bars
            for track_data in dsl_composition.get("tracks", []):
                # Insert track
                track_insert = {
                    "composition_id": composition_id,
                    "name": track_data["name"]
                }
                track_id = await self.track_repo.insert(session, track_insert)
                
                # 3. Insert track bars
                for bar_data in track_data.get("bars", []):
                    track_bar_insert = {
                        "track_id": track_id,
                        "bar_index": bar_data["bar_index"],
                        "clip_id": bar_data["clip_id"],
                        "clip_bar_index": bar_data["clip_bar_index"]
                    }
                    await self.track_bar_repo.insert(session, track_bar_insert)
            
            return composition_id
    
    async def get_composition_with_tracks(self, composition_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a complete composition with all its tracks and track bars.
        
        Args:
            composition_id: ID of the composition
        
        Returns:
            Dictionary with composition, tracks, and track bars, or None if not found
        """
        async with self.db.session() as session:
            # Get composition
            composition = await self.composition_repo.get_by_id(session, composition_id)
            if not composition:
                return None
            
            # Get tracks
            tracks = await self.track_repo.find_by_composition_id(session, composition_id)
            
            # Get track bars for each track
            for track in tracks:
                track["bars"] = await self.track_bar_repo.find_by_track_id(session, track["id"])
            
            composition["tracks"] = tracks
            return composition
    
    async def find_compositions_by_name(self, name_pattern: str) -> List[Dict[str, Any]]:
        """
        Search compositions by name pattern.
        
        Args:
            name_pattern: Pattern to search for (e.g., "%symphony%")
        
        Returns:
            List of composition dictionaries
        """
        async with self.db.session() as session:
            return await self.composition_repo.search_by_name(session, name_pattern)
    
    async def find_compositions_by_tempo(self, min_tempo: int, max_tempo: int) -> List[Dict[str, Any]]:
        """
        Find compositions within a tempo range.
        
        Args:
            min_tempo: Minimum tempo BPM
            max_tempo: Maximum tempo BPM
        
        Returns:
            List of composition dictionaries
        """
        async with self.db.session() as session:
            return await self.composition_repo.find_by_tempo_range(session, min_tempo, max_tempo)
    
    async def get_track_by_name(self, composition_id: int, track_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific track from a composition by name.
        
        Args:
            composition_id: ID of the composition
            track_name: Name of the track
        
        Returns:
            Track dictionary with bars, or None if not found
        """
        async with self.db.session() as session:
            track = await self.track_repo.find_by_name(session, composition_id, track_name)
            if not track:
                return None
            
            track["bars"] = await self.track_bar_repo.find_by_track_id(session, track["id"])
            return track
    
    async def delete_composition(self, composition_id: int) -> bool:
        """
        Delete a composition and all its associated tracks and track bars.
        
        Args:
            composition_id: ID of the composition to delete
        
        Returns:
            True if deleted, False if not found
        """
        async with self.db.session() as session:
            # Cascade delete will handle tracks and track bars
            return await self.composition_repo.delete_by_id(session, composition_id)
    
    async def list_all_compositions(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List all compositions (optionally limited).
        
        Args:
            limit: Optional limit on number of compositions
        
        Returns:
            List of composition dictionaries
        """
        async with self.db.session() as session:
            return await self.composition_repo.get_all(session, limit=limit)
