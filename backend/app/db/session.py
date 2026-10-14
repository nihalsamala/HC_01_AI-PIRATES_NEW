"""
Database session helper for WardPulse.

SQLite at backend/wardpulse.db (git-ignored).
Provides get_db() dependency for FastAPI and a standalone engine/session factory.
"""

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Base

# Database file lives next to the backend/ root
_DB_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
_DB_PATH = _DB_DIR / "wardpulse.db"
DATABASE_URL = f"sqlite:///{_DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables (idempotent)."""
    Base.metadata.create_all(bind=engine)


def reset_db() -> None:
    """Drop and recreate all tables."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and auto-closes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- For testing: allow overriding with a temp database ---
_test_session_factory = None


def override_session_factory(factory):
    """Override the session factory for testing."""
    global _test_session_factory
    _test_session_factory = factory


def get_session() -> Session:
    """Get a session, respecting test overrides."""
    if _test_session_factory is not None:
        return _test_session_factory()
    return SessionLocal()
