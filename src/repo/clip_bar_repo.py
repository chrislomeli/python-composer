# src/repo/clip_bar_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.repo.models import ClipBarModel

class ClipBarRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_clip_bar(self, clip_bar: ClipBarModel) -> int:
        sql = text("""
            INSERT INTO clip_bar
            (clip_id, bar_index, velocity_curve, cc, pitch_bend_curve, aftertouch_curve, pedal_events, metadata)
            VALUES (:clip_id, :bar_index, :velocity_curve, :cc, :pitch_bend_curve, :aftertouch_curve, :pedal_events, :metadata)
            RETURNING id
        """)
        # convert lists/dicts to JSON strings
        params = clip_bar.model_dump()
        for k in ["velocity_curve", "cc", "pitch_bend_curve", "aftertouch_curve", "pedal_events", "metadata"]:
            if params.get(k) is not None:
                import json
                params[k] = json.dumps(params[k])
        result = await self.session.execute(sql, params)
        clip_bar_id = result.scalar()
        await self.session.commit()
        return clip_bar_id
