"""Exact reviewed schema bytes; no resolver, validator execution or source grant."""

import base64
import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import SchemaRef
from amphora_contracts_graph_runtime import DefinitionSchema

from ..context.policy import require
from ..context.snapshot import _constant, _object
from .universe import ReviewedUniverse, canonical


@dataclass(frozen=True)
class SchemaObservation:
    universe: ReviewedUniverse
    canonical: bytes
    body: bytes

    @classmethod
    def bind(cls, universe, selected, supplied):
        universe = ReviewedUniverse.bind(universe.document(), universe.request)
        selected = SchemaRef.model_validate(selected.model_dump(mode="python", warnings=False))
        require(selected in universe.document().schemas, "runtime_schema_unselected")
        require(type(supplied) is DefinitionSchema, "runtime_metadata_type")
        value = DefinitionSchema.model_validate(supplied.model_dump(mode="python", warnings=False))
        require(value.scope == universe.document().scope and value.universe_sha256 == universe.sha256 and
                value.reference == selected, "runtime_schema_identity")
        body = base64.b64decode(value.schema_bytes_base64, validate=True)
        require(hashlib.sha256(body).hexdigest() == selected.sha256, "runtime_schema_digest")
        try:
            document = json.loads(body.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
            require(type(document) in (dict, bool), "runtime_schema_document")
            # Detect overflowing JSON floats without altering the original bytes.
            json.dumps(document, allow_nan=False)
        except (ValueError, RecursionError):
            raise ValueError("runtime_schema_document") from None
        return cls(universe, canonical(value.model_dump(mode="json")), body)

    def document(self):
        return DefinitionSchema.model_validate_json(self.canonical)
