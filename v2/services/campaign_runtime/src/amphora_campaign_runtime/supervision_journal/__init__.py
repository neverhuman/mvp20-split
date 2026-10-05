"""Immutable request origins; persistence and execution authority are separate."""

from .frames import RequestFrame
from .series import RequestSeries

__all__ = ['RequestFrame', 'RequestSeries']
