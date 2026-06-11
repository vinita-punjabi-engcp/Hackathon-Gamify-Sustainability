"""
EcoTrace AI entrypoint.

The application is assembled in src/api/main.py (factory) with logic split
across src/api (routes/schemas) and src/services (business logic). This module
stays thin so that `python3 app.py` and `uvicorn app:app` both keep working.
"""
import uvicorn

from src.api.main import app  # noqa: F401 — re-exported so `uvicorn app:app` resolves

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
