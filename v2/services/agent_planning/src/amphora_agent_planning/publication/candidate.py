"""Shared exact observed candidate/source/finalized interpretation binding."""

import hashlib
from dataclasses import dataclass, replace

from amphora_contracts_artifacts import FinalizedReceipt
from amphora_contracts_knowledge import ClaimGrounding

from ..context import AttemptBinding
from ..context.policy import require
from ..extraction import ExtractionSnapshot, SourceBundle, TraceProjection
from ..extraction.trace import CandidateOrigins
from ..persistence.records import verified_observation
from ..providers.profiles import OutputProfiles
from .payload import TraceArtifact


@dataclass(frozen=True)
class PublishedCandidate:
    task: ExtractionSnapshot
    candidate_bytes: bytes
    sources: SourceBundle
    interpretation_bytes: bytes

    @classmethod
    def from_publication(cls, task, observation, review, publication):
        task = ExtractionSnapshot.from_bytes(task.canonical, task.request)
        require(review.task.canonical == task.canonical, "validation_task_binding")
        sources = SourceBundle.bind(task, review.bundle.sources)
        require(publication.payload is not None and publication.attempt is not None and
                publication.attempt.stage == "finalized", "interpretation_not_published")
        attempt = publication.attempt
        result = attempt.result
        require(result is not None, "interpretation_receipt_missing")
        receipt = FinalizedReceipt(upload_id=result.upload_id, artifact=result.artifact)
        require(replace(attempt, stage="finalizing", result=None).finalized(
            publication.identity, publication.payload.artifact, receipt, result) == attempt,
            "interpretation_receipt_binding")
        projection = TraceProjection(publication.payload.artifact.body)
        artifact = TraceArtifact.reviewed(publication.identity, projection, review)
        require(artifact == publication.payload.artifact, "interpretation_payload_binding")
        trace = projection.document()
        binding = AttemptBinding(task.request, trace.attempt.ordinal)
        observation = verified_observation(binding, observation)
        wire = observation.document()
        require(wire.attempt == trace.attempt and wire.proposal is not None, "interpretation_candidate_missing")
        require(trace.outcome.observation_sha256 == hashlib.sha256(observation.canonical).hexdigest() and
                trace.outcome.candidate_sha256 == wire.proposal.payload_sha256 and
                trace.outcome.status == wire.status and trace.outcome.capture_sha256 == wire.output_sha256,
                "interpretation_observation_binding")
        draft = OutputProfiles.draft_model(task.request.document().context.output_schema).model_validate_json(
            wire.proposal.payload_json)
        require(trace.fields == CandidateOrigins(draft).fields() and trace.diagnostics == draft.diagnostics,
                "interpretation_attribution_binding")
        return cls(task, wire.proposal.payload_json.encode("utf-8"), sources,
                   result.artifact.model_dump_json().encode("utf-8"))

    def draft(self):
        return OutputProfiles.draft_model(self.task.request.document().context.output_schema).model_validate_json(
            self.candidate_bytes)

    def interpretation(self):
        from amphora_contracts_core import ArtifactRef
        return ArtifactRef.model_validate_json(self.interpretation_bytes)

    def grounding(self, attributions):
        spans, traces = [], []
        for attribution in attributions:
            self.sources.verify_attribution(attribution)
            for quotation in attribution.quotations:
                if quotation.span not in spans:
                    spans.append(quotation.span)
                source = next(source for source in self.task.document().sources if source.source == quotation.span.source)
                for trace in source.conversion_traces:
                    if trace not in traces:
                        traces.append(trace)
        require(0 < len(spans) <= 64 and 0 < len(traces) <= 64, "proposal_grounding_limit")
        return ClaimGrounding(spans=tuple(spans), conversion_traces=tuple(traces),
                              interpretation_artifacts=(self.interpretation(),))
