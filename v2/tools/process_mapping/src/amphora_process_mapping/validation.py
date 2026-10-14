"""Owner-local population-json-v1 boundary validation; no peer-private imports."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef


def require(condition, code):
    if not condition:
        raise ValueError(code)


def canonical(record):
    return json.dumps(record.model_dump(mode="json"), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def consistent_references(references):
    known = {}
    for reference in references:
        require(known.setdefault(reference.artifact_id, reference) == reference, "process_reference_conflict")


@dataclass(frozen=True)
class PopulationArtifact:
    reference: ArtifactRef
    content: bytes

    def decode(self, model, schema, scope):
        reference = ArtifactRef.model_validate_json(self.reference.model_dump_json())
        require(reference.scope == scope and reference.schema_ref == schema and reference.media_type == "application/json",
                "process_artifact_binding")
        require(type(self.content) is bytes and len(self.content) <= 262144, "process_artifact_bytes")
        require(reference.size_bytes == len(self.content) and reference.sha256 == hashlib.sha256(self.content).hexdigest(),
                "process_artifact_digest")
        record = model.model_validate_json(self.content)
        require(canonical(record) == self.content, "process_artifact_canonical")
        return record
