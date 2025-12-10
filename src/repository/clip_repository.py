# clip_repository.py
# Async repository for clips table

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.schema import clips
from src.repository.base_repository import BaseRepository


class ClipRepository(BaseRepository):
    """Async repository for managing clips in the database."""
    
    def __init__(self):
        super().__init__(clips)
    
    async def find_by_name(self, session: AsyncSession, name: str) -> List[Dict[str, Any]]:
        """
        Find clips by name (exact match).
        
        Args:
            session: SQLAlchemy async session
            name: Clip name to search for
        
        Returns:
            List of clip dictionaries
        """
        return await self.find_by(session, name=name)
    
    async def find_by_track_name(self, session: AsyncSession, track_name: str) -> List[Dict[str, Any]]:
        """
        Find clips by track name.
        
        Args:
            session: SQLAlchemy async session
            track_name: Track name to search for
        
        Returns:
            List of clip dictionaries
        """
        return await self.find_by(session, track_name=track_name)
    
    async def search_by_name(self, session: AsyncSession, name_pattern: str) -> List[Dict[str, Any]]:
        """
        Search clips by name pattern (case-insensitive).
        
        Args:
            session: SQLAlchemy async session
            name_pattern: Pattern to search for (e.g., "%lead%")
        
        Returns:
            List of clip dictionaries
        """
        stmt = select(self.table).where(
            self.table.c.name.ilike(name_pattern)
        )
        result = await session.execute(stmt)
        results = result.fetchall()
        return [dict(row._mapping) for row in results]
    
    async def find_by_tags(self, session: AsyncSession, tags: List[str]) -> List[Dict[str, Any]]:
        """
        Find clips that have any of the specified tags.
        
        Args:
            session: SQLAlchemy async session
            tags: List of tags to search for
        
        Returns:
            List of clip dictionaries
        """
        from sqlalchemy import func, cast, String
        
        stmt = select(self.table).where(
            self.table.c.tags.isnot(None)
        )
        result = await session.execute(stmt)
        results = result.fetchall()
        
        matching_clips = []
        for row in results:
            clip_dict = dict(row._mapping)
            clip_tags = clip_dict.get("tags", []) or []
            if any(tag in clip_tags for tag in tags):
                matching_clips.append(clip_dict)
        
        return matching_clips
