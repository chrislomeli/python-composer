# composition_repository.py
# Async repository for compositions table

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.schema import compositions
from src.repository.base_repository import BaseRepository


class CompositionRepository(BaseRepository):
    """Async repository for managing compositions in the database."""
    
    def __init__(self):
        super().__init__(compositions)
    
    async def find_by_name(self, session: AsyncSession, name: str) -> List[Dict[str, Any]]:
        """
        Find compositions by name (exact match).
        
        Args:
            session: SQLAlchemy async session
            name: Composition name to search for
        
        Returns:
            List of composition dictionaries
        """
        return await self.find_by(session, name=name)
    
    async def search_by_name(self, session: AsyncSession, name_pattern: str) -> List[Dict[str, Any]]:
        """
        Search compositions by name pattern (case-insensitive).
        
        Args:
            session: SQLAlchemy async session
            name_pattern: Pattern to search for (e.g., "%symphony%")
        
        Returns:
            List of composition dictionaries
        """
        stmt = select(self.table).where(
            self.table.c.name.ilike(name_pattern)
        )
        result = await session.execute(stmt)
        results = result.fetchall()
        return [dict(row._mapping) for row in results]
    
    async def find_by_tempo_range(
        self, 
        session: AsyncSession, 
        min_tempo: int, 
        max_tempo: int
    ) -> List[Dict[str, Any]]:
        """
        Find compositions within a tempo range.
        
        Args:
            session: SQLAlchemy async session
            min_tempo: Minimum tempo BPM (inclusive)
            max_tempo: Maximum tempo BPM (inclusive)
        
        Returns:
            List of composition dictionaries
        """
        stmt = select(self.table).where(
            (self.table.c.tempo_bpm >= min_tempo) &
            (self.table.c.tempo_bpm <= max_tempo)
        )
        result = await session.execute(stmt)
        results = result.fetchall()
        return [dict(row._mapping) for row in results]
