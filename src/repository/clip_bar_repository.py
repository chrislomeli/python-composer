# clip_bar_repository.py
# Async repository for clip_bars table

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.schema import clip_bars
from src.repository.base_repository import BaseRepository


class ClipBarRepository(BaseRepository):
    """Async repository for managing clip bars in the database."""
    
    def __init__(self):
        super().__init__(clip_bars)
    
    async def find_by_clip_id(self, session: AsyncSession, clip_id: int) -> List[Dict[str, Any]]:
        """
        Find all bars for a given clip, ordered by bar_index.
        
        Args:
            session: SQLAlchemy async session
            clip_id: ID of the clip
        
        Returns:
            List of clip bar dictionaries, ordered by bar_index
        """
        stmt = (
            select(self.table)
            .where(self.table.c.clip_id == clip_id)
            .order_by(self.table.c.bar_index)
        )
        result = await session.execute(stmt)
        results = result.fetchall()
        return [dict(row._mapping) for row in results]
    
    async def get_by_clip_and_bar(
        self, 
        session: AsyncSession, 
        clip_id: int, 
        bar_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific bar from a clip.
        
        Args:
            session: SQLAlchemy async session
            clip_id: ID of the clip
            bar_index: Index of the bar within the clip
        
        Returns:
            Clip bar dictionary, or None if not found
        """
        stmt = select(self.table).where(
            (self.table.c.clip_id == clip_id) &
            (self.table.c.bar_index == bar_index)
        )
        result = await session.execute(stmt)
        row = result.first()
        return dict(row._mapping) if row else None
    
    async def find_with_expression(self, session: AsyncSession, expression_type: str) -> List[Dict[str, Any]]:
        """
        Find clip bars that have a specific type of expression curve.
        
        Args:
            session: SQLAlchemy async session
            expression_type: Type of expression (e.g., 'velocity_curve', 'cc', 'pitch_bend_curve')
        
        Returns:
            List of clip bar dictionaries
        """
        column = getattr(self.table.c, expression_type, None)
        if column is None:
            return []
        
        stmt = select(self.table).where(column.isnot(None))
        result = await session.execute(stmt)
        results = result.fetchall()
        return [dict(row._mapping) for row in results]
