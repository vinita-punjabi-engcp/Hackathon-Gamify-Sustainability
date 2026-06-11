"""FastAPI dependencies shared across API routes."""
from src.db.session import SessionLocal


def get_db():
    """Yields a SQLAlchemy session and guarantees it is closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
