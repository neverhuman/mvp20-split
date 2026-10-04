"""Byte-owned interpretation projection from verified task/attempt facts."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_planning import (
    ExtractionDraft,
    ExtractionDraftV2,
    ExtractionTrace,
    ExtractionTraceRef,
    InterpretationOrigin,
    InterpretationOutcome,
)

from ..context import AttemptBinding
from ..context.policy import require
from ..persistence.records import verified_observation
from ..providers.profiles import OutputProfiles
from .snapshot import ExtractionSnapshot


@dataclass(frozen=True)
class CandidateOrigins:
    draft: ExtractionDraft | ExtractionDraftV2

    def fields(self):
        result = []
        for path, item in OutputProfiles.attributed_items(self.draft):
            attribution = item.attribution
            result.append(InterpretationOrigin(
                target_path=path,
                origin="model_claimed_source" if attribution.origin == "source_stated" else "model_inferred",
                confidence=attribution.confidence,
                spans=tuple(quote.span for quote in attribution.quotations)))
            for field in ("applicability", "validation_method", "context", "method", "required_context"):
                if hasattr(item, field) and getattr(item, field) is None:
                    result.append(self.missing(f"{path}/{field}"))
        paths = {item.target_path for item in result if item.origin == "missing"}
        for diagnostic in self.draft.diagnostics:
            if diagnostic.kind == "missing" and diagnostic.target_path not in paths:
                result.append(self.missing(diagnostic.target_path))
                paths.add(diagnostic.target_path)
        return tuple(result)

    @staticmethod
    def missing(path):
        return InterpretationOrigin(target_path=path, origin="missing", confidence="unknown", spans=())


@dataclass(frozen=True)
class TraceProjection:
    canonical: bytes

    @classmethod
    def derive(cls, trace_id, task, observation, prior=None):
        task = ExtractionSnapshot.from_bytes(task.canonical, task.request)
        require(observation is not None, "extraction_attempt_pending")
        wire = observation.document()
        binding = AttemptBinding(task.request, wire.attempt.ordinal)
        observation = verified_observation(binding, observation)
        wire = observation.document()
        require(wire.schema_version == "2", "extraction_observation_profile")
        document = task.document()
        context = task.request.document().context
        parent = None if prior is None else prior.document()
        if parent is not None:
            require(parent.scope == document.scope and parent.sources == document.sources and
                    parent.target == document.target, "extraction_repair_binding")
            require(parent.trace_id != trace_id and parent.attempt != wire.attempt,
                    "extraction_repair_identity")
            require(parent.repair_depth < 16, "extraction_repair_depth")
        draft = None if wire.proposal is None else OutputProfiles.draft_model(context.output_schema).model_validate_json(
            wire.proposal.payload_json)
        outcome = InterpretationOutcome(
            observation_sha256=hashlib.sha256(observation.canonical).hexdigest(),
            capture_sha256=wire.output_sha256, captured_bytes=wire.captured_bytes,
            capture_complete=wire.output_complete, status=wire.status, reason_code=wire.reason_code,
            candidate_sha256=None if wire.proposal is None else wire.proposal.payload_sha256)
        # These are verified local transformations. A request model/prompt pin does
        # not prove that an unavailable/rejected provider actually ran that model.
        transforms = tuple({"transform_id": name, "version": "1", "configuration_sha256": digest,
                            "kind": "deterministic"} for name, digest in (
                                ("extraction_task_binding", task.sha256),
                                ("extraction_observation_verification", context.output_schema.sha256)))
        record = ExtractionTrace.model_validate_json(json.dumps({
            "scope": document.scope.model_dump(mode="json"), "trace_id": trace_id,
            "task_id": document.task_id, "task_sha256": task.sha256,
            "attempt": wire.attempt.model_dump(mode="json"),
            "sources": [source.model_dump(mode="json") for source in document.sources],
            "target": document.target.model_dump(mode="json"), "model": context.model.model_dump(mode="json"),
            "prompt": context.prompt.model_dump(mode="json"), "policy": context.policy.model_dump(mode="json"),
            "transforms": transforms, "outcome": outcome.model_dump(mode="json"),
            "fields": [] if draft is None else [field.model_dump(mode="json") for field in CandidateOrigins(draft).fields()],
            "diagnostics": [] if draft is None else [item.model_dump(mode="json") for item in draft.diagnostics],
            "prior": None if prior is None else prior.reference().model_dump(mode="json"),
            "repair_depth": 0 if parent is None else parent.repair_depth + 1,
        }))
        raw = json.dumps(record.model_dump(mode="json"), sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
        require(len(raw) <= 1048576, "extraction_trace_size")
        return cls(raw)

    def document(self):
        return ExtractionTrace.model_validate_json(self.canonical)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def reference(self):
        document = self.document()
        return ExtractionTraceRef(scope=document.scope, trace_id=document.trace_id, sha256=self.sha256)
