import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Determine DB URL and check if fallback is needed
db_url = settings.DATABASE_URL
if not db_url.startswith("postgresql+asyncpg://"):
    # If the user specified a standard postgresql url, convert it to asyncpg
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

class DBContainer:
    def __init__(self):
        self.engine = create_async_engine(db_url, echo=True, future=True)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

db = DBContainer()
Base = declarative_base()

async def init_db():
    # If postgres fails, we try to catch the exception and fall back to SQLite
    try:
        async with db.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"PostgreSQL connection failed ({e}). Falling back to local SQLite database...")
        fallback_url = "sqlite+aiosqlite:///./aicrm.db"
        db.engine = create_async_engine(fallback_url, echo=True, future=True)
        db.async_session = sessionmaker(
            db.engine, class_=AsyncSession, expire_on_commit=False
        )
        async with db.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with db.async_session() as session:
        try:
            yield session
        finally:
            await session.close()
