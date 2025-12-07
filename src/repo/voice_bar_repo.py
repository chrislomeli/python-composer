# src/repo/voice_bar_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.repo.models import VoiceBarModel

class VoiceBarRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_voice_bar(self, vb: VoiceBarModel) -> int:
        sql = text("""
            INSERT INTO voice_bar
            (clip_id, bar_number, time_signature_numerator, time_signature_denominator, metadata)
            VALUES (:clip_id, :bar_number, :time_signature_numerator, :time_signature_denominator, :metadata)
            RETURNING id
        """)
        result = await self.session.execute(sql, vb.dict())
        bar_id = result.scalar()
        await self.session.commit()
        return bar_id

    async def get_voice_bar_by_id(self, bar_id: int) -> VoiceBarModel:
        sql = text("SELECT * FROM voice_bar WHERE id = :bar_id")
        result = await self.session.execute(sql, {"bar_id": bar_id})
        row = result.fetchone()
        return VoiceBarModel(**dict(row)) if row else None
