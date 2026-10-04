"""Immutable trace content and full source-reviewed derived input declaration."""

import hashlib
import json
from dataclasses import dataclass
from importlib.resources import files

from amphora_contracts_artifacts import ContentDescriptor, DerivationDeclaration, TransformationDescriptor
from amphora_contracts_core import SchemaRef
from amphora_contracts_evidence import ConversionTrace, SourceRevision

from ..context.policy import require
from ..extraction import ExtractionSnapshot, PromptTemplate, SourceBundle
from ..source_access.review import canonical


def content_schema_bytes():
    return files("amphora_agent_planning.publication").joinpath("extraction-trace-v1.schema.json").read_bytes()


def content_schema():
    return SchemaRef(schema_id="planning.extraction-trace-content", version="1",
                     sha256=hashlib.sha256(content_schema_bytes()).hexdigest())


@dataclass(frozen=True)
class TraceArtifact:
    body: bytes
    content: ContentDescriptor
    declaration: DerivationDeclaration

    @classmethod
    def reviewed(cls, identity, projection, review):
        task = ExtractionSnapshot.from_bytes(review.task.canonical, review.task.request)
        document = task.document()
        request = task.request.document()
        trace = projection.document()
        require(identity.trace() == projection.reference(), "publication_trace_binding")
        require(identity.actor_id == request.actor_id, "publication_actor_binding")
        require(trace.task_id == document.task_id and trace.task_sha256 == task.sha256 and
                trace.attempt.engagement == document.engagement and trace.attempt.request_sha256 == task.request.sha256,
                "publication_task_binding")
        context = request.context
        require(trace.sources == document.sources and trace.target == document.target and trace.model == context.model and
                trace.prompt == context.prompt and trace.policy == context.policy, "publication_trace_provenance")
        bundle = SourceBundle.bind(task, review.bundle.sources)
        prompt = PromptTemplate.bind(context.prompt, review.prompt.instructions)
        require(prompt.canonical_reference == review.prompt.canonical_reference, "publication_prompt_binding")
        revisions = tuple(SourceRevision.model_validate_json(raw) for raw in review.source_documents)
        require(tuple(row.reference for row in revisions) == tuple(row.source for row in document.sources),
                "publication_source_review")
        traces = tuple(ConversionTrace.model_validate_json(raw) for raw in review.trace_documents)
        expected_traces = [(item.source, ref) for item in document.sources for ref in item.conversion_traces]
        require(len(traces) == len(expected_traces) and all(
            trace.source == source and trace.scope == ref.scope and trace.trace_id == ref.trace_id and
            hashlib.sha256(canonical(trace)).hexdigest() == ref.sha256
            for trace, (source, ref) in zip(traces, expected_traces, strict=True)), "publication_trace_review")
        inputs = review.inputs()
        by_id = {reference.artifact_id: reference for reference in inputs}
        require(len(inputs) == len(by_id) and 0 < len(inputs) <= 128, "publication_input_count")
        require(all(ref.scope == document.scope for ref in inputs), "publication_input_scope")
        required = (context.objective, context.prompt, context.policy, context.model.configuration,
                    *(entry.artifact for entry in context.entries), *(row.descriptor().source.raw for row in bundle.sources))
        required += tuple(trace.output for trace in traces)
        require(all(by_id.get(ref.artifact_id) == ref for ref in required), "publication_input_missing")
        require(set(by_id) == {ref.artifact_id for ref in required}, "publication_input_unreviewed")
        body = canonical(trace)
        require(body == projection.canonical and len(body) <= 1048576, "publication_trace_bytes")
        content = ContentDescriptor(sha256=projection.sha256, size_bytes=len(body),
                                    media_type="application/json", schema_ref=content_schema())
        method = json.dumps({"profile": "planning.extraction-interpretation.v1", "task_sha256": task.sha256,
                             "trace_sha256": projection.sha256,
                             "observation_sha256": trace.outcome.observation_sha256},
                            sort_keys=True, separators=(",", ":")).encode("utf-8")
        declaration = DerivationDeclaration(transformation=TransformationDescriptor(
            transformation_id="planning.extraction_interpretation", version="1",
            sha256=hashlib.sha256(method).hexdigest()), inputs=tuple(by_id[key] for key in sorted(by_id)))
        return cls(body, content, declaration)
