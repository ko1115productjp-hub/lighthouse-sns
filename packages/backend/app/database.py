"""
Database connection and session management
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from app.config import settings

# Supabase Transaction Pooler (port 6543) does not support prepared statements.
# Switch to Session Pooler (port 5432) which does support them.
database_url = settings.DATABASE_URL
if ":6543/" in database_url:
    database_url = database_url.replace(":6543/", ":5432/")

# Create async engine
# Use NullPool for serverless environments (Vercel) - no connection pooling
engine = create_async_engine(
    database_url,
    echo=settings.DEBUG,
    future=True,
    poolclass=NullPool,  # Disable connection pooling for serverless
    connect_args={
        "statement_cache_size": 0,  # Disable prepared statement cache for pgbouncer
        "server_settings": {
            "application_name": "lighthouse_backend",
        },
    },
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create declarative base for models
Base = declarative_base()


async def get_db():
    """Dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
