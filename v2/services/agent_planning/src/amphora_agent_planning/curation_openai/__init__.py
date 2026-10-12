"""Explicit synthetic curation provider; worker owns durable once-only issuance."""
from .adapter import CurationOpenAI

__all__ = ['CurationOpenAI']
