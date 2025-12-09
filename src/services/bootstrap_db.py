import asyncio
import os

from src.repository import get_database
from src.core.schema import metadata

async def main():
    DATABASE_URL = os.getenv("DATABASE_URL")
    db = get_database()  # uses DATABASE_URL
    await db.create_tables(metadata)

if __name__ == "__main__":
    asyncio.run(main())