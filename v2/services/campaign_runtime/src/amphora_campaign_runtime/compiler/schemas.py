"""Hash-verified local schemas and conservative typed projections; never fetch references."""

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from urllib.parse import unquote

from jsonschema import Draft202012Validator, validators
from jsonschema.exceptions import SchemaError

from .errors import CompilationError, require
from .shapes import ScalarShape, SchemaIdentity

_MAPPINGS = {"properties", "patternProperties", "$defs", "definitions", "dependentSchemas"}
_SINGLES = {"items", "additionalProperties", "unevaluatedProperties", "unevaluatedItems", "contains", "not", "if", "then", "else", "propertyNames"}
_ARRAYS = {"allOf", "anyOf", "oneOf", "prefixItems"}


def _pairs(values):
    result = {}
    for key, value in values:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _reject_constant(_value):
    raise ValueError("nonfinite_json")


def _finite_float(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("nonfinite_json")
    return result


def _freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(child) for key, child in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(child) for child in value)
    return value


@dataclass(frozen=True, init=False)
class PinnedSchema:
    identity: SchemaIdentity
    _document: object
    _body: bytes
    _formats: frozenset

    def __init__(self, identity, body):
        location = identity.name
        require(isinstance(body, bytes) and len(body) <= 65536, "schema_size_limit", location)
        require(hashlib.sha256(body).hexdigest() == identity.digest, "schema_digest_mismatch", location)
        try:
            document = json.loads(body, object_pairs_hook=_pairs, parse_constant=_reject_constant, parse_float=_finite_float)
            require(isinstance(document, (dict, bool)), "invalid_schema_document", location)
            Draft202012Validator.check_schema(document)
        except (ValueError, UnicodeError, RecursionError, SchemaError) as error:
            raise CompilationError("invalid_schema_document", location) from error
        object.__setattr__(self, "identity", identity)
        object.__setattr__(self, "_body", body)
        object.__setattr__(self, "_document", document)
        pending, count, seen, references, formats = [(document, 0)], 0, set(), [], set()
        while pending:
            node, depth = pending.pop()
            count += 1
            require(depth <= 64 and count <= 4096, "schema_complexity_limit", location)
            if isinstance(node, bool):
                continue
            seen.add(id(node))
            if "format" in node:
                formats.add(node["format"])
            require(not any(key in node for key in ("$id", "$dynamicRef", "$dynamicAnchor", "$anchor")),
                    "unsupported_schema_reference", location)
            require(node.get("$schema", "https://json-schema.org/draft/2020-12/schema") == "https://json-schema.org/draft/2020-12/schema",
                    "unsupported_schema_dialect", location)
            if "$ref" in node:
                references.append(self._target(node["$ref"]))
            for key in _MAPPINGS:
                pending.extend((child, depth + 1) for child in node.get(key, {}).values())
            for key in _SINGLES:
                if key in node:
                    pending.append((node[key], depth + 1))
            for key in _ARRAYS:
                pending.extend((child, depth + 1) for child in node.get(key, ()))
        require(all(isinstance(target, bool) or id(target) in seen for target in references),
                "invalid_schema_reference_target", location)
        try:
            object.__setattr__(self, "_document", _freeze(document))
            object.__setattr__(self, "_formats", frozenset(formats))
        except RecursionError as error:
            raise CompilationError("schema_complexity_limit", location) from error

    @property
    def source_bytes(self):
        """Exact immutable reviewed bytes, for owner-local retained compilation material."""
        return self._body

    def _target(self, reference):
        require(isinstance(reference, str) and (reference == "#" or reference.startswith("#/")),
                "external_schema_reference", self.identity.name)
        node = self._document
        if reference == "#":
            return node
        try:
            for raw in unquote(reference[2:]).split("/"):
                require(not any(raw[index] == "~" and (index + 1 == len(raw) or raw[index + 1] not in "01")
                                for index in range(len(raw))), "unresolved_schema_reference", self.identity.name)
                key = raw.replace("~1", "/").replace("~0", "~")
                if isinstance(node, (list, tuple)):
                    require(key == "0" or (key.isascii() and key.isdecimal() and not key.startswith("0")),
                            "unresolved_schema_reference", self.identity.name)
                    node = node[int(key)]
                else:
                    node = node[key]
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise CompilationError("unresolved_schema_reference", self.identity.name) from error
        require(isinstance(node, (Mapping, bool)), "invalid_schema_reference_target", self.identity.name)
        return node

    def _resolve(self, node, location):
        visited = set()
        annotations = {"$ref", "title", "description", "default", "examples", "deprecated", "readOnly", "writeOnly", "$comment", "x-amphora-unit"}
        unit = None
        while isinstance(node, Mapping) and "$ref" in node:
            require(not set(node) - annotations, "unsupported_projection_reference", location)
            reference = node["$ref"]
            require(reference not in visited and len(visited) < 64, "cyclic_projection_reference", location)
            visited.add(reference)
            unit = node.get("x-amphora-unit", unit)
            node = self._target(reference)
        require(isinstance(node, Mapping) and not any(key in node for key in ("anyOf", "oneOf", "allOf", "not", "if")),
                "unsupported_projection_schema", location)
        return node if unit is None else {**node, "x-amphora-unit": unit}

    def binding_target(self, path, location):
        """Resolve a finite declared schema path; return an immutable schema fragment."""
        node = self._resolve(self._document, location)
        for step in path:
            if isinstance(step, str):
                require(node.get("type") == "object" and step in node.get("properties", {}), "unknown_projection_property", location)
                node = node["properties"][step]
            else:
                require(node.get("type") == "array", "projection_not_array", location)
                require(step < node.get("maxItems", 10001), "projection_out_of_bounds", location)
                prefix = node.get("prefixItems", ())
                node = prefix[step] if step < len(prefix) else node.get("items", True)
            node = self._resolve(node, location)
        return node

    def validate(self, value):
        """Validate actual JSON against the exact local pin, preserving decimal numbers."""
        from ..lifecycle.model import TransitionError

        if not self._formats <= set(Draft202012Validator.FORMAT_CHECKER.checkers):
            raise TransitionError("binding_schema_format_unsupported")
        checker = Draft202012Validator.TYPE_CHECKER.redefine("integer", lambda _checker, item:
            type(item) is int or isinstance(item, Decimal) and item.is_finite() and item == item.to_integral_value())
        validator = validators.extend(Draft202012Validator, type_checker=checker)(
            json.loads(self._body, parse_float=Decimal), format_checker=Draft202012Validator.FORMAT_CHECKER)
        try:
            valid = validator.is_valid(value)
        except (ValueError, TypeError, RecursionError, ArithmeticError) as error:
            raise TransitionError("binding_schema_invalid") from error
        if not valid:
            raise TransitionError("binding_schema_invalid")

    def project(self, path, parent_unit, location):
        node = self.binding_target(path, location)
        kind = node.get("type")
        require(isinstance(kind, str) and kind in {"boolean", "integer", "number", "string"}, "projection_not_scalar", location)
        unit = node.get("x-amphora-unit", parent_unit if kind in {"integer", "number"} else "1")
        require(isinstance(unit, str) and 1 <= len(unit) <= 64 and (kind in {"integer", "number"} or unit == "1"),
                "invalid_projection_unit", location)
        return ScalarShape(kind, unit)


class SchemaCatalog:
    def __init__(self, schemas):
        schemas = tuple(schemas)
        entries = {schema.identity: schema for schema in schemas}
        require(len(entries) == len(schemas), "duplicate_schema_identity", "schemas")
        self._entries = MappingProxyType(entries)

    def require(self, identity, location):
        value = self._entries.get(identity)
        require(value is not None, "unknown_schema_pin", location)
        return value
