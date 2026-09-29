"""Revalidate owner inputs before serialization can normalize invalid constructed DTOs."""

from pydantic import BaseModel


def raw_fields(value):
    if isinstance(value, BaseModel):
        return {key: raw_fields(item) for key, item in value}
    if isinstance(value, tuple):
        return tuple(raw_fields(item) for item in value)
    if isinstance(value, list):
        return [raw_fields(item) for item in value]
    if isinstance(value, dict):
        return {key: raw_fields(item) for key, item in value.items()}
    return value
