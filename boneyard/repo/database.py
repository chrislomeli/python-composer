# boneyard/repo/service.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.repo.models import DatabaseLogin



class Database:
    def __init__(self, dsn: DatabaseLogin):
        self.engine = create_async_engine(dsn.toURL(), echo=False, future=True)
        self.session_factory = sessionmaker(self.engine,  expire_on_commit=False, class_=AsyncSession ) # type: ignore

    async def get_session(self):
        async with self.session_factory() as session:
            yield session
