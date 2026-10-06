"""Trusted, hash-bound JSON Schema profiles; never resolve network references."""

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


def json_value(payload: bytes):
    def unique(pairs):
        result = {}
        for key, item in pairs:
            key.encode("utf-8")
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = item
        return result

    def invalid(_value):
        raise ValueError("Non-finite JSON constant")

    value = json.loads(payload.decode("utf-8"), object_pairs_hook=unique, parse_constant=invalid)
    pending = [(value, 1)]
    while pending:
        item, depth = pending.pop()
        if depth > 64:
            raise ValueError("Content nesting exceeded")
        if isinstance(item, dict):
            pending.extend((v, depth + 1) for v in item.values())
        elif isinstance(item, list):
            pending.extend((v, depth + 1) for v in item)
        elif isinstance(item, float) and not math.isfinite(item):
            raise ValueError("Non-finite JSON number")
        elif isinstance(item, str):
            item.encode("utf-8")
    return value


@dataclass(frozen=True, slots=True)
class JsonSchemaRule:
    identity: tuple[str, str, str, str]
    document: bytes

    def __post_init__(self):
        if (self.identity[0] != "application/json" or len(self.document) > 65536
            or hashlib.sha256(self.document).hexdigest() != self.identity[3]):
            raise ValueError("Invalid schema profile identity or size")
        schema = json_value(self.document)
        if not isinstance(schema, dict):
            raise ValueError("Schema object required")
        Draft202012Validator.check_schema(schema)
        checker = FormatChecker()
        pending = [schema]
        seen = set()
        while pending:
            item = pending.pop()
            if isinstance(item, dict):
                if id(item) in seen:
                    continue
                seen.add(id(item))
                # Canonical root URN labels the exact pinned document; it cannot
                # introduce nested resources or authorize external resolution.
                if "$id" in item and (item is not schema or
                    item["$id"] != f"urn:amphora:{self.identity[1]}:{self.identity[2]}:validation"):
                    raise ValueError("Schema reference profile unsupported")
                if any(key in item for key in ("$dynamicRef", "$dynamicAnchor", "$anchor", "$recursiveRef")):
                    raise ValueError("Schema reference profile unsupported")
                if "$ref" in item and (not isinstance(item["$ref"], str)
                    or not item["$ref"].startswith("#/")):
                    raise ValueError("Only local JSON pointer references supported")
                if "$ref" in item:
                    target = schema
                    try:
                        for segment in item["$ref"][2:].split("/"):
                            segment = segment.replace("~1", "/").replace("~0", "~")
                            target = target[int(segment)] if isinstance(target, list) else target[segment]
                        if not isinstance(target, (dict, bool)):
                            raise ValueError("Schema reference must target a schema")
                    except (KeyError, IndexError, TypeError) as error:
                        raise ValueError("Unresolved local schema reference") from error
                    pending.append(target)
                if "$schema" in item and item["$schema"] != "https://json-schema.org/draft/2020-12/schema":
                    raise ValueError("JSON Schema 2020-12 required")
                if "format" in item and item["format"] not in checker.checkers:
                    raise ValueError("Unsupported schema format")
                # Only schema positions; property names/defaults are ordinary user data.
                for key in ("$defs", "definitions", "properties", "patternProperties", "dependentSchemas"):
                    pending.extend(item.get(key, {}).values())
                for key in ("allOf", "anyOf", "oneOf", "prefixItems"):
                    pending.extend(item.get(key, []))
                for key in ("additionalProperties", "unevaluatedProperties", "propertyNames", "contains",
                            "items", "unevaluatedItems", "not", "if", "then", "else", "contentSchema"):
                    if key in item:
                        pending.append(item[key])

    @classmethod
    def from_path(cls, identity, path):
        with Path(path).open("rb") as source:
            document = source.read(65537)
        return cls(identity, document)

    def validate(self, value):
        # Rebuild from immutable bytes: callers cannot mutate the trusted validator.
        validator = Draft202012Validator(json_value(self.document), format_checker=FormatChecker())
        try:
            valid = validator.is_valid(value)
        except Exception as error:
            # Includes unresolved local references; no payload detail crosses the owner boundary.
            raise ValueError("Schema validation failed") from error
        if not valid:
            raise ValueError("Schema validation failed")


def configured_profiles(profiles, directory):
    allowed, rules = set(), []
    fields = {"media_type", "schema_id", "version", "sha256"}
    for profile in profiles:
        if set(profile) not in (fields, fields | {"schema_path"}):
            raise ValueError("Invalid content profile configuration")
        identity = tuple(profile[key] for key in ("media_type", "schema_id", "version", "sha256"))
        if identity in allowed:
            raise ValueError("Duplicate content profile")
        allowed.add(identity)
        if "schema_path" in profile:
            rules.append(JsonSchemaRule.from_path(identity, Path(directory) / profile["schema_path"]))
    return frozenset(allowed), tuple(rules)
