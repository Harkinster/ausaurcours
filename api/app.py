"""FastAPI application entry point.

This module exposes the fully configured application located in
``ausaur.app`` so deployment targets can simply import ``app`` from the
project root (``uvicorn app:app``).
"""

from ausaur.app import app

__all__ = ["app"]
