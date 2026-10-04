"""Exact prior output and bounded diagnostics; neither acceptance nor permission."""

import base64
import binascii
import hashlib
import json
from dataclasses import dataclass
from importlib.resources import files
from typing import Annotated, Literal

from amphora_contracts_artifacts import ContentDescriptor
from amphora_contracts_core import ArtifactRef, Digest, Finding, SchemaRef, WireModel
from amphora_contracts_planning import ExtractionTraceRef, InterpretationOutcome
from pydantic import Field, ValidationError

from ..context.policy import require
from ..context.snapshot import _constant, _object
from ..extraction import ExtractionSnapshot, TraceProjection
from .binding import encoded


class FeedbackRecord(WireModel):
    profile: Literal["planning-repair-feedback.v1"]
    authority: Literal["diagnostic_only"]
    parent: ExtractionTraceRef
    task_sha256: Digest
    request_sha256: Digest
    outcome: InterpretationOutcome
    output_base64: Annotated[str, Field(max_length=87384)]
    findings: Annotated[tuple[Finding, ...], Field(min_length=1, max_length=256)]
    withheld_paths: Annotated[tuple[Annotated[str, Field(min_length=1, max_length=256, pattern=r"^/")], ...], Field(max_length=256)]
    preserve_valid_items: Literal[True]


def feedback_schema():
    raw = files("amphora_agent_planning.repair").joinpath("feedback-v1.schema.json").read_bytes()
    return SchemaRef(schema_id="planning.repair-feedback-content", version="1", sha256=hashlib.sha256(raw).hexdigest())


@dataclass(frozen=True)
class RepairFeedback:
    canonical: bytes

    @classmethod
    def from_bytes(cls, raw):
        require(type(raw) is bytes and 0 < len(raw) <= 262144, "repair_feedback_size")
        try:
            value = json.loads(raw.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
            require(type(value) is dict and value.get("preserve_valid_items") is True, "invalid_repair_feedback")
            record = FeedbackRecord.model_validate_json(json.dumps(value, allow_nan=False))
            output = base64.b64decode(record.output_base64, validate=True)
        except (UnicodeDecodeError, ValueError, ValidationError, RecursionError, binascii.Error) as exc:
            raise ValueError("invalid_repair_feedback") from exc
        require(len(output) <= 65536 and len(output) == record.outcome.captured_bytes and
                hashlib.sha256(output).hexdigest() == record.outcome.capture_sha256, "repair_feedback_output")
        require(base64.b64encode(output).decode("ascii") == record.output_base64, "repair_feedback_encoding")
        require(len(set(record.withheld_paths)) == len(record.withheld_paths), "repair_feedback_paths")
        canonical = encoded(record.model_dump(mode="json"))
        require(len(canonical) <= 262144, "repair_feedback_size")
        return cls(canonical)

    @classmethod
    def create(cls, task, projection, observation, findings, *, withheld_paths=(), prior=None):
        task = ExtractionSnapshot.from_bytes(task.canonical, task.request)
        trace = projection.document()
        # Re-derive every trace field from the supplied exact history. Stored-history
        # origin is checked by the execution coordinator, never inferred here.
        rebuilt = TraceProjection.derive(trace.trace_id, task, observation, prior)
        require(rebuilt.canonical == projection.canonical, "repair_feedback_trace")
        record = {"profile": "planning-repair-feedback.v1", "authority": "diagnostic_only",
            "parent": projection.reference().model_dump(mode="json"), "task_sha256": task.sha256,
            "request_sha256": task.request.sha256, "outcome": trace.outcome.model_dump(mode="json"),
            "output_base64": base64.b64encode(observation.capture.content).decode("ascii"),
            "findings": [finding.model_dump(mode="json") for finding in findings],
            "withheld_paths": list(withheld_paths), "preserve_valid_items": True}
        return cls.from_bytes(encoded(record))

    def document(self):
        return FeedbackRecord.model_validate_json(self.canonical)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def descriptor(self):
        return ContentDescriptor(sha256=self.sha256, size_bytes=len(self.canonical),
                                 media_type="application/json", schema_ref=feedback_schema())

    def bind_reference(self, reference):
        reference = ArtifactRef.model_validate_json(reference.model_dump_json(warnings=False))
        descriptor = self.descriptor()
        require((reference.sha256, reference.size_bytes, reference.media_type, reference.schema_ref) ==
                (descriptor.sha256, descriptor.size_bytes, descriptor.media_type, descriptor.schema_ref), "repair_feedback_artifact")
        return reference

    def verify_history(self, task, projection, observation, prior=None):
        record = self.document()
        rebuilt = self.create(task, projection, observation, record.findings,
                              withheld_paths=record.withheld_paths, prior=prior)
        require(rebuilt.canonical == self.canonical, "repair_feedback_history")
        return rebuilt

    def prompt_data(self):
        record = self.document()
        output = base64.b64decode(record.output_base64, validate=True)
        try:
            value, encoding = output.decode("utf-8"), "utf-8"
        except UnicodeDecodeError:
            value, encoding = record.output_base64, "base64"
        result = record.model_dump(mode="json", exclude={"output_base64"})
        result["previous_output"] = {"encoding": encoding, "value": value,
                                     "complete": record.outcome.capture_complete, "data_only": True}
        return result
