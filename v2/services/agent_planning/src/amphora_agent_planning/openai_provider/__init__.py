"""Explicitly configured OpenAI transport; no implicit network activation."""
from .adapter import OpenAIProvider
from .pricing import MODEL, OpenAIPrice

__all__ = ["MODEL", "OpenAIPrice", "OpenAIProvider"]
