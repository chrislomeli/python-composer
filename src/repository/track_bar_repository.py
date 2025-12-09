# track_bar_repository.py
# Async repository for track_bars table

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.schema import track_bars
from src.repository.base_repository import BaseRepository


class TrackBarRepository(BaseRepository):
    """Async repository for managing track bars in the database."""
    
    def __init__(self):
        super().__init__(track_bars)
    
    async def find_by_track_id(self, session: AsyncSession, track_id: int) -> List[Dict[str, Any]]:
        """
        Find all bars for a given track, ordered by bar_index.
        
        Args:
            session: SQLAlchemy async session
            track_id: ID of the track
        
        Returns:
            List of track bar dictionaries, ordered by bar_index
        """
        stmt = (
            select(self.table)
            .where(self.table.c.track_id == track_id)
            .order_by(self.table.c.bar_index)
        )
        result = await session.execute(stmt)
        results = result.fetchall()
        return [dict(row._mapping) for row in results]
    
    async def find_by_clip_id(self, session: AsyncSession, clip_id: int) -> List[Dict[str, Any]]:
        """
        Find all track bars that reference a specific clip.
        
        Args:
            session: SQLAlchemy async session
            clip_id: ID of the clip
        
        Returns:
            List of track bar dictionaries
        """
        return await self.find_by(session, clip_id=clip_id)
    
    async def get_by_track_and_bar(
        self, 
        session: AsyncSession, 
        track_id: int, 
        bar_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific bar from a track.
        
        Args:
            session: SQLAlchemy async session
            track_id: ID of the track
            bar_index: Index of the bar within the track
        
        Returns:
            Track bar dictionary, or None if not found
        """
        stmt = select(self.table).where(
            (self.table.c.track_id == track_id) &
            (self.table.c.bar_index == bar_index)
        )
        result = await session.execute(stmt)
        row = result.first()
        return dict(row._mapping) if row else None
