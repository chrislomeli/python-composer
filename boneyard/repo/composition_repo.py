# boneyard/repo/composition_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.repo.models import CompositionModel

class CompositionRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_composition(self, composition: CompositionModel) -> int:
        sql = text("""
            INSERT INTO composition
            (name, ticks_per_quarter, tempo_bpm, time_signature_numerator, time_signature_denominator, metadata)
            VALUES (:name, :ticks_per_quarter, :tempo_bpm, :time_signature_numerator, :time_signature_denominator, :metadata)
            RETURNING id
        """)
        result = await self.session.execute(sql, composition.dict())
        comp_id = result.scalar()
        await self.session.commit()
        return comp_id

    async def get_composition_by_name(self, name: str) -> CompositionModel:
        sql = text("SELECT * FROM composition WHERE name = :name")
        result = await self.session.execute(sql, {"name": name})
        row = result.fetchone()
        return CompositionModel(**dict(row)) if row else None
