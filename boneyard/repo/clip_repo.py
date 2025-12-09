# boneyard/repo/clip_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.repo.models import ClipModel

class ClipRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_clip(self, clip: ClipModel) -> int:
        sql = text("""
            INSERT INTO clips (name, style, instrument, tempo_bpm, grid_units, metadata)
            VALUES (:name, :style, :instrument, :tempo_bpm, :grid_units, :metadata)
            RETURNING id
        """)
        result = await self.session.execute(sql, clip.dict())
        clip_id = result.scalar()
        await self.session.commit()
        return clip_id

    async def get_clip_by_id(self, clip_id: int) -> ClipModel:
        sql = text("SELECT * FROM clips WHERE id = :clip_id")
        result = await self.session.execute(sql, {"clip_id": clip_id})
        row = result.fetchone()
        return ClipModel(**dict(row)) if row else None
