from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config import get_settings
from db.models import Base


def get_engine():
    settings = get_settings()
    engine = create_engine(settings.database_url, echo=False)
    return engine


def init_db():
    """Create the pgvector extension and all tables."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(engine)


def get_session():
    """Get a new DB session."""
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
