# boneyard/repo/note_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.repo.models import NoteModel

class NoteRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_note(self, note: NoteModel) -> int:
        sql = text("""
            INSERT INTO notes
            (bar_id, start_unit, duration_units, pitch_name, octave,
             velocity, articulation, is_rest,
             expression, microtiming_offset, metadata)
            VALUES (:bar_id, :start_unit, :duration_units, :pitch_name, :octave,
                    :velocity, :articulation, :is_rest,
                    :expression, :microtiming_offset, :metadata)
            RETURNING id
        """)
        result = await self.session.execute(sql, note.dict())
        note_id = result.scalar()
        await self.session.commit()
        return note_id

    async def get_notes_by_bar(self, bar_id: int) -> list[NoteModel]:
        sql = text("SELECT * FROM notes WHERE bar_id = :bar_id ORDER BY start_unit")
        result = await self.session.execute(sql, {"bar_id": bar_id})
        rows = result.fetchall()
        return [NoteModel(**dict(row)) for row in rows]
