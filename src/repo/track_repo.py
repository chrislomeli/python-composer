# src/repo/track_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.repo.models import TrackModel  # your Pydantic model


class TrackRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_track(self, track: TrackModel) -> int:
        """
        Insert a track into the track table.
        """
        sql = text("""
            INSERT INTO track
            (composition_id, name, instrument, midi_channel, group_id, position, metadata)
            VALUES (:composition_id, :name, :instrument, :midi_channel, :group_id, :position, :metadata)
            RETURNING id
        """)
        result = await self.session.execute(sql, track.model_dump())
        track_id = result.scalar()
        await self.session.commit()
        return track_id
