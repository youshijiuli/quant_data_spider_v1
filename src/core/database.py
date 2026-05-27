"""SQLAlchemy engine, session, and dependency injection."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.models import Base


def create_db_engine(database_url: str):
    return create_engine(
        database_url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False,
    )


def create_session_factory(engine):
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db(database_url: str) -> tuple:
    """Initialize database engine and session factory.

    Returns (engine, SessionLocal). Caller is responsible for lifecycle.
    """
    engine = create_db_engine(database_url)
    SessionLocal = create_session_factory(engine)
    return engine, SessionLocal


def create_all_tables(engine) -> None:
    """Create all tables defined in models. Use Alembic in production."""
    Base.metadata.create_all(bind=engine)


def get_db_session(session_factory) -> Session:
    """Yield a database session, closing it automatically."""
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
