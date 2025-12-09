# note_repository.py
# Async repository for notes table

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.schema import notes
from src.repository.base_repository import BaseRepository


class NoteRepository(BaseRepository):
    """Async repository for managing notes in the database."""
    
    def __init__(self):
        super().__init__(notes)
    
    async def find_by_clip_bar_id(self, session: AsyncSession, clip_bar_id: int) -> List[Dict[str, Any]]:
        """
        Find all notes for a given clip bar, ordered by start_beat.
        
        Args:
            session: SQLAlchemy async session
            clip_bar_id: ID of the clip bar
        
        Returns:
            List of note dictionaries, ordered by start_beat
        """
        stmt = (
            select(self.table)
            .where(self.table.c.clip_bar_id == clip_bar_id)
            .order_by(self.table.c.start_beat)
        )
        result = await session.execute(stmt)
        results = result.fetchall()
        return [dict(row._mapping) for row in results]
    
    async def find_rests(self, session: AsyncSession, clip_bar_id: int) -> List[Dict[str, Any]]:
        """
        Find all rest notes in a clip bar.
        
        Args:
            session: SQLAlchemy async session
            clip_bar_id: ID of the clip bar
        
        Returns:
            List of rest note dictionaries
        """
        stmt = select(self.table).where(
            (self.table.c.clip_bar_id == clip_bar_id) &
            (self.table.c.is_rest == True)
        )
        result = await session.execute(stmt)
        results = result.fetchall()
        return [dict(row._mapping) for row in results]
    
    async def find_by_pitch_range(
        self, 
        session: AsyncSession, 
        clip_bar_id: int,
        min_pitch: int, 
        max_pitch: int
    ) -> List[Dict[str, Any]]:
        """
        Find notes within a pitch range.
        
        Args:
            session: SQLAlchemy async session
            clip_bar_id: ID of the clip bar
            min_pitch: Minimum MIDI pitch (inclusive)
            max_pitch: Maximum MIDI pitch (inclusive)
        
        Returns:
            List of note dictionaries
        """
        stmt = select(self.table).where(
            (self.table.c.clip_bar_id == clip_bar_id) &
            (self.table.c.pitch >= min_pitch) &
            (self.table.c.pitch <= max_pitch) &
            (self.table.c.is_rest == False)
        )
        result = await session.execute(stmt)
        results = result.fetchall()
        return [dict(row._mapping) for row in results]
    
    async def get_pitch_range(self, session: AsyncSession, clip_bar_id: int) -> Optional[tuple[int, int]]:
        """
        Get the min and max pitch in a clip bar.
        
        Args:
            session: SQLAlchemy async session
            clip_bar_id: ID of the clip bar
        
        Returns:
            Tuple of (min_pitch, max_pitch), or None if no notes
        """
        from sqlalchemy import func
        
        stmt = select(
            func.min(self.table.c.pitch),
            func.max(self.table.c.pitch)
        ).where(
            (self.table.c.clip_bar_id == clip_bar_id) &
            (self.table.c.is_rest == False)
        )
        result = await session.execute(stmt)
        row = result.first()
        
        if row and row[0] is not None:
            return (row[0], row[1])
        return None
