# boneyard/repo/test_clip_builder.py
import json
import asyncio

from src.service.loader.composition_loader import load_composition
from src.repo.database import Database, DatabaseLogin

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
        # Load JSON
        composition = json.load(open("/boneyard/service/loader/test_composition.json"))
        composition_id = await load_composition(session=session, composition_json=composition)
        print("Created clip ID:", composition_id)

if __name__ == "__main__":
    asyncio.run(main())
