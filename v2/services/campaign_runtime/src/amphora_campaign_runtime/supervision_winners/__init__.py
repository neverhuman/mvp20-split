"""Runtime-owned atomic checkpoint winner; no provider or Data calls."""

from .storage import WinnerStore

__all__ = ['WinnerStore']
