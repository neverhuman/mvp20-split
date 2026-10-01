"""Small bounded string/null object profile with exact token byte offsets."""

import json
from dataclasses import dataclass

from .provenance import ProvenanceError


@dataclass(frozen=True)
class LocatedValue:
    value: str | None
    start: int
    end: int


def parse_fields(content: bytes, allowed: frozenset[str]) -> dict[str, LocatedValue]:
    if len(content) > 65536:
        raise ProvenanceError("lab_input_limit")
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ProvenanceError("invalid_utf8") from error
    decoder = json.JSONDecoder()
    size = len(text)

    def whitespace(index):
        while index < size and text[index] in " \t\n\r":
            index += 1
        return index

    def token(index):
        try:
            value, end = decoder.raw_decode(text, index)
        except (ValueError, RecursionError) as error:
            raise ProvenanceError("invalid_lab_json") from error
        if value is not None and not isinstance(value, str):
            raise ProvenanceError("lab_requires_string_or_null")
        if isinstance(value, str):
            try:
                value.encode("utf-8", errors="strict")
            except UnicodeEncodeError as error:
                raise ProvenanceError("invalid_unicode_scalar") from error
            if len(value) > 2048:
                raise ProvenanceError("lab_field_limit")
        return value, end

    index = whitespace(0)
    if index >= size or text[index] != "{":
        raise ProvenanceError("lab_requires_object")
    index = whitespace(index + 1)
    fields = {}
    if index < size and text[index] == "}":
        index += 1
    else:
        while True:
            if index >= size or text[index] != '"':
                raise ProvenanceError("invalid_lab_json")
            key, index = token(index)
            if key not in allowed:
                raise ProvenanceError("unknown_lab_field")
            if key in fields:
                raise ProvenanceError("duplicate_lab_field")
            index = whitespace(index)
            if index >= size or text[index] != ":":
                raise ProvenanceError("invalid_lab_json")
            start = whitespace(index + 1)
            if start >= size or text[start] not in ('"', 'n'):
                raise ProvenanceError("lab_requires_string_or_null")
            value, end = token(start)
            fields[key] = LocatedValue(value, len(text[:start].encode("utf-8")), len(text[:end].encode("utf-8")))
            index = whitespace(end)
            if index < size and text[index] == "}":
                index += 1
                break
            if index >= size or text[index] != ",":
                raise ProvenanceError("invalid_lab_json")
            index = whitespace(index + 1)
    if whitespace(index) != size:
        raise ProvenanceError("trailing_lab_content")
    return fields
