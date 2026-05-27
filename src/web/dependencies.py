"""FastAPI dependency injection."""

from fastapi import Request
from sqlalchemy.orm import Session

from config.settings import Settings
from src.acquisition.source_registry import SourceRegistry

_registry: SourceRegistry | None = None


def get_db(request: Request) -> Session:
    """Yield a database session, closing it after the request."""
    session: Session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_settings(request: Request) -> Settings:
    from config.settings import settings
    return settings


def get_source_registry() -> SourceRegistry:
    global _registry
    if _registry is None:
        _registry = SourceRegistry()
    return _registry
