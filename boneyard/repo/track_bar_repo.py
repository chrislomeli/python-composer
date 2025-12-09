# boneyard/repo/track_bar_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.repo.models import TrackBarModel


class TrackBarRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_track_bar(self, track_bar: TrackBarModel) -> int:
        """
        Insert a track_bar entry. Can reference a clip or a voice_bar.
        """
        sql = text("""
            INSERT INTO track_bar
            (track_id, bar_index, voice_bar_id, clip_id, clip_bar_index, is_empty, metadata)
            VALUES (:track_id, :bar_index, :voice_bar_id, :clip_id, :clip_bar_index, :is_empty, :metadata)
            RETURNING id
        """)
        result = await self.session.execute(sql, track_bar.model_dump())
        track_bar_id = result.scalar()
        await self.session.commit()
        return track_bar_id
