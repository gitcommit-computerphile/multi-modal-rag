from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config import get_settings
from db.models import Base


@lru_cache(maxsize=1)
def get_engine():
    """Process-wide engine. Cached because each engine owns a connection pool —
    building one per request means a fresh TCP connect + auth handshake every time."""
    settings = get_settings()
    return create_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )


@lru_cache(maxsize=1)
def _get_sessionmaker():
    return sessionmaker(bind=get_engine())


def init_db():
    """Create the pgvector extension and all tables."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(engine)


def get_session():
    """Get a new DB session from the shared pool."""
    return _get_sessionmaker()()
