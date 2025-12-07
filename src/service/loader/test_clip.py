# src/repo/test_clip_builder.py
import json
import asyncio

from src.service.loader.clip_loader import ClipBuilder
from src.repo.database import Database, DatabaseLogin
from src.repo.note_repo import NoteRepo
from src.repo.clip_repo import ClipRepo
from src.repo.voice_bar_repo import VoiceBarRepo

DB_NAME = "music"
DB_USER = "postgres"
DB_PASS = "BlackKaiser=1"
DB_HOST = "127.0.0.1"
DB_PORT = 5432

async def main():
    # Initialize Database (AsyncEngine)
    db = Database(
        DatabaseLogin(database=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
    )

    # Create a single async session
    async with db.session_factory() as session:
        # Create repos with the same session
        clip_repo = ClipRepo(session)
        note_repo = NoteRepo(session)
        vb_repo = VoiceBarRepo(session)

        # Pass repos into the builder
        builder = ClipBuilder(clip_repo, note_repo, vb_repo)

        # Load JSON
        clip_data = json.load(open("test_clip.json"))
        for clip in clip_data:
            clip_id = await builder.load_clip_from_json(clip)
            print("Created clip ID:", clip_id)

if __name__ == "__main__":
    asyncio.run(main())
