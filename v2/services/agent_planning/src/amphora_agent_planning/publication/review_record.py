"""Immutable historical review metadata, never a reusable rights lease."""

import json
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef, Digest
from amphora_contracts_evidence import ConversionTrace, SourceRevision
from pydantic import TypeAdapter

from ..context.policy import require
from ..context.snapshot import _constant, _object
from ..extraction import ExtractionSnapshot, PromptTemplate, SourceBundle


@dataclass(frozen=True)
class ReviewRecord:
    canonical: bytes

    @classmethod
    def from_review(cls, review):
        task = ExtractionSnapshot.from_bytes(review.task.canonical, review.task.request)
        SourceBundle.bind(task, review.bundle.sources)
        prompt = PromptTemplate.bind(task.request.document().context.prompt, review.prompt.instructions)
        require(prompt.canonical_reference == review.prompt.canonical_reference, "publication_prompt_binding")
        value = {"format": "planning-trace-source-review.v1", "task_sha256": task.sha256,
                 "artifacts": [json.loads(raw) for raw in review.artifact_documents],
                 "sources": [json.loads(raw) for raw in review.source_documents],
                 "traces": [json.loads(raw) for raw in review.trace_documents]}
        return cls.from_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                         ensure_ascii=False, allow_nan=False).encode("utf-8"))

    @classmethod
    def from_bytes(cls, raw):
        require(type(raw) is bytes and 0 < len(raw) <= 4194304, "publication_review_size")
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
        require(type(value) is dict and set(value) == {"format", "task_sha256", "artifacts", "sources", "traces"}
                and value["format"] == "planning-trace-source-review.v1", "publication_review_format")
        TypeAdapter(Digest).validate_python(value["task_sha256"], strict=True)
        for key, model, maximum in (("artifacts", ArtifactRef, 128), ("sources", SourceRevision, 16),
                                    ("traces", ConversionTrace, 128)):
            require(type(value[key]) is list and len(value[key]) <= maximum, "publication_review_count")
            value[key] = [model.model_validate_json(json.dumps(item)).model_dump(mode="json") for item in value[key]]
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                             allow_nan=False).encode("utf-8")
        require(encoded == raw, "publication_review_canonical")
        return cls(encoded)

    def document(self):
        return json.loads(self.canonical)

    def records(self, key, model):
        return tuple(model.model_validate_json(json.dumps(item)) for item in self.document()[key])
