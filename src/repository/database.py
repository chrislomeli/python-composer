# database.py
# Async database connection pool and session management

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator
import os


class Database:
    """
    Manages async database connection pool and provides session management.
    Singleton pattern for shared connection pool across the application.
    """
    
    def __init__(self, connection_string: Optional[str] = None, echo: bool = False):
        """
        Initialize async database connection pool.
        
        Args:
            connection_string: SQLAlchemy async connection string. 
                             If None, reads from DATABASE_URL env var.
                             Must use async driver (e.g., postgresql+asyncpg, sqlite+aiosqlite)
            echo: If True, log all SQL statements (useful for debugging)
        """
        if connection_string is None:
            connection_string = os.getenv(
                "DATABASE_URL",
                "postgresql+asyncpg://localhost:5432/music_composition"
            )
        
        # Convert standard connection strings to async versions
        if connection_string.startswith("postgresql://"):
            connection_string = connection_string.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif connection_string.startswith("sqlite://"):
            connection_string = connection_string.replace("sqlite://", "sqlite+aiosqlite://", 1)
        
        # Create async engine with connection pooling
        # SQLite doesn't support pool_size/max_overflow, so only use for other databases
        engine_kwargs = {
            "pool_pre_ping": True,  # Verify connections before using
            "echo": echo
        }
        
        # Only add pooling params for non-SQLite databases
        if not connection_string.startswith("sqlite"):
            engine_kwargs["pool_size"] = 10        # Max 10 connections in pool
            engine_kwargs["max_overflow"] = 20     # Allow 20 additional connections if pool is full
        
        self.engine: AsyncEngine = create_async_engine(connection_string, **engine_kwargs)
        
        # Create async session factory
        self.SessionLocal = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Provide a transactional scope for async database operations.
        
        Usage:
            async with db.session() as session:
                await session.execute(...)
                # Automatically commits on success, rolls back on exception
        
        Yields:
            SQLAlchemy AsyncSession object
        """
        async with self.SessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    def get_session(self) -> AsyncSession:
        """
        Get a new async session (caller is responsible for closing).
        Prefer using the session() context manager instead.
        
        Returns:
            SQLAlchemy AsyncSession object
        """
        return self.SessionLocal()
    
    async def create_tables(self, metadata):
        """
        Create all tables defined in metadata.
        
        Args:
            metadata: SQLAlchemy MetaData object with table definitions
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(metadata.create_all)
    
    async def drop_tables(self, metadata):
        """
        Drop all tables defined in metadata.
        WARNING: This will delete all data!
        
        Args:
            metadata: SQLAlchemy MetaData object with table definitions
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(metadata.drop_all)
    
    async def close(self):
        """Close all connections in the pool."""
        await self.engine.dispose()


# Singleton instance - import this in your repositories
_db_instance: Optional[Database] = None


def get_database(connection_string: Optional[str] = None, echo: bool = False) -> Database:
    """
    Get or create the singleton database instance.
    
    Args:
        connection_string: SQLAlchemy connection string (only used on first call)
        echo: If True, log SQL statements (only used on first call)
    
    Returns:
        Database instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(connection_string, echo)
    return _db_instance


def reset_database():
    """Reset the singleton database instance (useful for testing)."""
    global _db_instance
    if _db_instance is not None:
        _db_instance.close()
        _db_instance = None


# Convenience alias
db = get_database
