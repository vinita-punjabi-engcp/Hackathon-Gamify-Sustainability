"""FastAPI application factory for EcoTrace AI."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.db import models  # noqa: F401 — ensure models are registered before create_all
from src.db.session import Base, engine


def create_app() -> FastAPI:
    """Builds and configures the FastAPI application instance."""
    # Compile all structural tables cleanly on startup
    Base.metadata.create_all(bind=engine)

    app = FastAPI(title="EcoTrace AI - Auto-Scaling GreenOps Engine", version="3.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    return app


app = create_app()
