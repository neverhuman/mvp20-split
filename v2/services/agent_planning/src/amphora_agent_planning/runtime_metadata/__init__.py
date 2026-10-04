"""Campaign-bound reviewed Runtime metadata, without compiler or admission authority."""

from .reader import RuntimeMetadataReader, SchemaFailure, SchemaReadResult
from .schemas import SchemaObservation
from .universe import ReviewedUniverse

__all__ = ["ReviewedUniverse", "RuntimeMetadataReader", "SchemaFailure", "SchemaObservation", "SchemaReadResult"]
