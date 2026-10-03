"""Explicit vector-content policy; shape and canonical bytes do not prove provenance."""

import json

from amphora_contracts_representations import RepresentationVector, representation_vector_schema

from ..profiles import VectorSpace
from ..validation import require
from ..vectors import Float32Vector


class VectorContentRule:
    @property
    def identity(self):
        ref = representation_vector_schema()
        return "application/json", ref.schema_id, ref.version, ref.sha256

    def validate(self, value):
        document = RepresentationVector.model_validate_json(
            json.dumps(value, ensure_ascii=False, allow_nan=False)
        )
        # Normalization/metric require the registry profile; this rule checks only byte representation.
        space = VectorSpace(document.dimensions, document.dtype, "none", "dot")
        vector = Float32Vector(space, bytes.fromhex(document.payload_hex))
        require(vector.sha256 == document.payload_sha256, "representation_vector_digest")
