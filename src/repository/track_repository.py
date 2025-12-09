# track_repository.py
# Async repository for tracks table

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.schema import tracks
from src.repository.base_repository import BaseRepository


class TrackRepository(BaseRepository):
    """Async repository for managing tracks in the database."""
    
    def __init__(self):
        super().__init__(tracks)
    
    async def find_by_composition_id(self, session: AsyncSession, composition_id: int) -> List[Dict[str, Any]]:
        """
        Find all tracks for a given composition.
        
        Args:
            session: SQLAlchemy async session
            composition_id: ID of the composition
        
        Returns:
            List of track dictionaries
        """
        return await self.find_by(session, composition_id=composition_id)
    
    async def find_by_name(
        self, 
        session: AsyncSession, 
        composition_id: int, 
        name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find a track by name within a composition.
        
        Args:
            session: SQLAlchemy async session
            composition_id: ID of the composition
            name: Track name to search for
        
        Returns:
            Track dictionary, or None if not found
        """
        stmt = select(self.table).where(
            (self.table.c.composition_id == composition_id) &
            (self.table.c.name == name)
        )
        result = await session.execute(stmt)
        row = result.first()
        return dict(row._mapping) if row else None
