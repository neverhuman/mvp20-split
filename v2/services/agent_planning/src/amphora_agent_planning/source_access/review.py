"""Exact public source provenance and fresh process-authorized bytes."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef
from amphora_contracts_evidence import ConversionTrace, SourceRevision

from ..context.policy import require
from ..extraction import ExtractionSnapshot, PromptTemplate, SourceBundle, SourceText
from .budget import ReadBudget


def canonical(record):
    return json.dumps(record.model_dump(mode="json"), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


@dataclass(frozen=True)
class ReviewedSources:
    task: ExtractionSnapshot
    bundle: SourceBundle
    prompt: PromptTemplate
    artifact_documents: tuple[bytes, ...]
    source_documents: tuple[bytes, ...]
    trace_documents: tuple[bytes, ...]

    def inputs(self):
        return tuple(ArtifactRef.model_validate_json(raw) for raw in self.artifact_documents)


class SourceReviewer:
    def __init__(self, data):
        self.data = data

    def review(self, task, budget=None):
        task = ExtractionSnapshot.from_bytes(task.canonical, task.request)
        session = _Review(self.data, task.document().scope, ReadBudget() if budget is None else budget)
        context = task.request.document().context
        # Every selected context input is declared as consumed. Never omit it from
        # derived ancestry because it happens not to appear in a candidate quote.
        for artifact in (context.objective, context.prompt, context.policy, context.model.configuration,
                         *(entry.artifact for entry in context.entries)):
            session.artifact(artifact)
        sources, revisions, traces = [], [], []
        for descriptor in task.document().sources:
            record = self.data.source(descriptor.source, session.budget)
            record = SourceRevision.model_validate_json(record.model_dump_json(warnings=False))
            require(record.reference == descriptor.source and record.rights.scope == session.scope,
                    "source_revision_binding")
            require(record.method.format == "utf8_document", "source_input_format")
            revisions.append(canonical(record))
            raw = session.artifact(descriptor.source.raw)
            sources.append(SourceText.bind(descriptor, raw))
            for reference in descriptor.conversion_traces:
                trace = self.data.trace(reference, session.budget)
                trace = ConversionTrace.model_validate_json(trace.model_dump_json(warnings=False))
                trace_bytes = canonical(trace)
                require(trace.scope == session.scope and trace.trace_id == reference.trace_id and
                        hashlib.sha256(trace_bytes).hexdigest() == reference.sha256, "source_trace_binding")
                require(trace.source == descriptor.source and trace.source_schema == descriptor.source.raw.schema_ref and
                        trace.target_schema == trace.output.schema_ref, "source_trace_provenance")
                session.artifact(trace.output)
                for field in trace.fields:
                    for span in field.spans:
                        require(span.source == descriptor.source, "source_trace_span_source")
                        require(0 <= span.start <= span.end <= len(raw), "source_trace_span_bounds")
                        require(hashlib.sha256(raw[span.start:span.end]).hexdigest() == span.sha256,
                                "source_trace_span_digest")
                traces.append(trace_bytes)
        bundle = SourceBundle.bind(task, tuple(sources))
        prompt = PromptTemplate.bind(context.prompt, session.artifact(context.prompt))
        session.budget.remaining()
        return ReviewedSources(task, bundle, prompt,
                               tuple(canonical(session.identities[key]) for key in sorted(session.identities)),
                               tuple(revisions), tuple(traces))


class _Review:
    def __init__(self, data, scope, budget):
        self.data, self.scope, self.budget = data, scope, budget
        self.identities, self.payloads = {}, {}

    def artifact(self, reference):
        reference = ArtifactRef.model_validate_json(reference.model_dump_json(warnings=False))
        require(reference.scope == self.scope, "source_artifact_scope")
        existing = self.identities.get(reference.artifact_id)
        require(existing is None or existing == reference, "source_artifact_conflict")
        if reference.artifact_id not in self.payloads:
            require(len(self.identities) < 128, "source_input_count")
            require(reference.size_bytes <= 4194304, "source_artifact_size")
            self.identities[reference.artifact_id] = reference
            actual = self.data.artifact(reference, self.budget)
            actual = ArtifactRef.model_validate_json(actual.model_dump_json(warnings=False))
            require(actual == reference, "source_artifact_binding")
            content = self.data.content(reference, self.budget)
            require(type(content) is bytes and len(content) == reference.size_bytes and
                    hashlib.sha256(content).hexdigest() == reference.sha256, "source_artifact_bytes")
            self.payloads[reference.artifact_id] = content
        return self.payloads[reference.artifact_id]
