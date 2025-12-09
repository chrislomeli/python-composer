# base_repository.py
# Async base repository class with common CRUD operations

from typing import List, Dict, Any, Optional
from sqlalchemy import Table, select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    """
    Base repository providing common CRUD operations for a single table.
    All specific repositories should inherit from this class.
    """
    
    def __init__(self, table: Table):
        """
        Initialize repository with a SQLAlchemy table.
        
        Args:
            table: SQLAlchemy Table object
        """
        self.table = table
    
    async def insert(self, session: AsyncSession, data: Dict[str, Any]) -> int:
        """
        Insert a single row and return its ID.
        
        Args:
            session: SQLAlchemy async session
            data: Dictionary of column names to values
        
        Returns:
            ID of inserted row
        """
        result = await session.execute(
            insert(self.table).values(**data)
        )
        return result.inserted_primary_key[0]
    
    async def insert_many(self, session: AsyncSession, data_list: List[Dict[str, Any]]) -> List[int]:
        """
        Insert multiple rows and return their IDs.
        
        Args:
            session: SQLAlchemy async session
            data_list: List of dictionaries with column names to values
        
        Returns:
            List of IDs of inserted rows
        """
        if not data_list:
            return []
        
        ids = []
        for data in data_list:
            result = await session.execute(
                insert(self.table).values(**data)
            )
            ids.append(result.inserted_primary_key[0])
        return ids
    
    async def get_by_id(self, session: AsyncSession, id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single row by ID.
        
        Args:
            session: SQLAlchemy async session
            id: Primary key value
        
        Returns:
            Dictionary of column names to values, or None if not found
        """
        stmt = select(self.table).where(self.table.c.id == id)
        result = await session.execute(stmt)
        row = result.first()
        return dict(row._mapping) if row else None
    
    async def get_all(self, session: AsyncSession, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all rows from the table.
        
        Args:
            session: SQLAlchemy async session
            limit: Optional limit on number of rows
        
        Returns:
            List of dictionaries with column names to values
        """
        stmt = select(self.table)
        if limit:
            stmt = stmt.limit(limit)
        
        result = await session.execute(stmt)
        results = result.fetchall()
        return [dict(row._mapping) for row in results]
    
    async def update_by_id(self, session: AsyncSession, id: int, data: Dict[str, Any]) -> bool:
        """
        Update a single row by ID.
        
        Args:
            session: SQLAlchemy async session
            id: Primary key value
            data: Dictionary of column names to new values
        
        Returns:
            True if row was updated, False if not found
        """
        result = await session.execute(
            update(self.table)
            .where(self.table.c.id == id)
            .values(**data)
        )
        return result.rowcount > 0
    
    async def delete_by_id(self, session: AsyncSession, id: int) -> bool:
        """
        Delete a single row by ID.
        
        Args:
            session: SQLAlchemy async session
            id: Primary key value
        
        Returns:
            True if row was deleted, False if not found
        """
        result = await session.execute(
            delete(self.table).where(self.table.c.id == id)
        )
        return result.rowcount > 0
    
    async def find_by(self, session: AsyncSession, **filters) -> List[Dict[str, Any]]:
        """
        Find rows matching the given filters.
        
        Args:
            session: SQLAlchemy async session
            **filters: Column names and values to filter by
        
        Returns:
            List of dictionaries with column names to values
        
        Example:
            await repo.find_by(session, name="test", style="latin")
        """
        stmt = select(self.table)
        
        for column_name, value in filters.items():
            if hasattr(self.table.c, column_name):
                column = getattr(self.table.c, column_name)
                stmt = stmt.where(column == value)
        
        result = await session.execute(stmt)
        results = result.fetchall()
        return [dict(row._mapping) for row in results]
    
    async def count(self, session: AsyncSession, **filters) -> int:
        """
        Count rows matching the given filters.
        
        Args:
            session: SQLAlchemy async session
            **filters: Column names and values to filter by
        
        Returns:
            Number of matching rows
        """
        from sqlalchemy import func
        
        stmt = select(func.count()).select_from(self.table)
        
        for column_name, value in filters.items():
            if hasattr(self.table.c, column_name):
                column = getattr(self.table.c, column_name)
                stmt = stmt.where(column == value)
        
        result = await session.execute(stmt)
        count = result.scalar()
        return count or 0
    
    async def exists(self, session: AsyncSession, id: int) -> bool:
        """
        Check if a row with the given ID exists.
        
        Args:
            session: SQLAlchemy async session
            id: Primary key value
        
        Returns:
            True if row exists, False otherwise
        """
        from sqlalchemy import func
        
        stmt = select(func.count()).select_from(self.table).where(self.table.c.id == id)
        result = await session.execute(stmt)
        count = result.scalar()
        return count > 0
