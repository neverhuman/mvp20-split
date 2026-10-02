"""Fresh rights-scoped reads establish provenance, never scientific truth."""

import hashlib
from datetime import UTC, datetime

from amphora_contracts_knowledge import AddAssertion, CorrectAssertion, ReferenceValidation

from ..authoring.canonical import KnowledgeError, digest
from ..authoring.references import ReferencedInputs
from .transport import ReadBudget


class ReferenceReviewer:
    def __init__(self, data, research):
        self.data, self.research = data, research

    def review(self, proposal):
        references = ReferencedInputs.collect(proposal)
        assertions = tuple(operation.assertion if isinstance(operation, AddAssertion) else operation.replacement
            for operation in proposal.operations if isinstance(operation, (AddAssertion, CorrectAssertion)))
        return self._review(proposal.graph, references, (proposal.grounding,), assertions)

    def review_reasoning(self, request, assertions):
        references = ReferencedInputs.collect_records(request.snapshot.graph, (request, assertions))
        return self._review(request.snapshot.graph, references, (), assertions)

    def _review(self, graph, references, groundings, assertions):
        session = _Review(self.data, self.research, graph.scope, ReadBudget())
        for ref in references.artifacts:
            session.artifact(ref)
        for ref in references.sources:
            session.source(ref)
        for span in references.spans:
            session.span(span)
        traces = {ref: session.trace(ref) for ref in references.traces}
        questions = {ref: session.question(ref) for ref in references.questions}
        needs = {ref: session.need(ref) for ref in references.needs}
        groundings = list(groundings)
        for assertion in assertions:
            groundings.append(assertion.grounding)
            for link in assertion.research_links:
                question = questions[link.question]
                if link.need is not None:
                    need = needs[link.need]
                    if need.question != question.reference:
                        raise KnowledgeError("need_question_mismatch")
                    if not set(need.criterion_ids) <= {item.criterion_id for item in question.criteria}:
                        raise KnowledgeError("need_criterion_mismatch")
        for grounding in groundings:
            local = [traces[ref] for ref in grounding.conversion_traces]
            for span in grounding.spans:
                if not any(trace.source == span.source for trace in local):
                    raise KnowledgeError("grounding_trace_mismatch")
            if any(not any(trace.source == span.source for span in grounding.spans) for trace in local):
                raise KnowledgeError("grounding_trace_mismatch")
        session.budget.remaining()
        return ReferenceValidation(checked_at=datetime.now(UTC), artifacts=references.artifacts,
            sources=references.sources, conversion_traces=references.traces,
            questions=references.questions, evidence_needs=references.needs)


class _Review:
    """Per-review cache: bounded bytes, exact identities, no cross-request rights cache."""

    def __init__(self, data, research, scope, budget):
        self.data, self.research, self.scope, self.budget = data, research, scope, budget
        self.payloads, self.sources = {}, {}
        self.identities = {}

    def scope_of(self, ref):
        if ref.scope != self.scope:
            raise KnowledgeError("reference_scope_mismatch")

    def artifact(self, ref):
        self.scope_of(ref)
        prior = self.identities.get(ref.artifact_id)
        if prior is not None and prior != ref:
            raise KnowledgeError("reference_identity_conflict")
        self.identities[ref.artifact_id] = ref
        if ref not in self.payloads:
            if len(self.payloads) >= 256:
                raise KnowledgeError("expanded_reference_limit")
            if self.data.artifact(ref, self.budget) != ref:
                raise KnowledgeError("artifact_binding_mismatch")
            raw = self.data.content(ref, self.budget)
            if len(raw) != ref.size_bytes or hashlib.sha256(raw).hexdigest() != ref.sha256:
                raise KnowledgeError("artifact_bytes_mismatch")
            self.payloads[ref] = raw
        return self.payloads[ref]

    def source(self, ref):
        self.scope_of(ref)
        if ref not in self.sources:
            if len(self.sources) >= 256:
                raise KnowledgeError("expanded_reference_limit")
            record = self.data.source(ref, self.budget)
            if record.reference != ref:
                raise KnowledgeError("source_binding_mismatch")
            self.scope_of(record.rights)
            self.artifact(ref.raw)
            self.sources[ref] = record
        return self.sources[ref]

    def span(self, span):
        self.source(span.source)
        raw = self.artifact(span.source.raw)
        if not 0 <= span.start <= span.end <= len(raw):
            raise KnowledgeError("source_span_bounds")
        if hashlib.sha256(raw[span.start:span.end]).hexdigest() != span.sha256:
            raise KnowledgeError("source_span_digest_mismatch")

    def trace(self, ref):
        self.scope_of(ref)
        trace = self.data.trace(ref, self.budget)
        if trace.scope != ref.scope or trace.trace_id != ref.trace_id or digest(trace) != ref.sha256:
            raise KnowledgeError("trace_binding_mismatch")
        self.source(trace.source)
        self.artifact(trace.output)
        for field in trace.fields:
            for span in field.spans:
                if span.source != trace.source:
                    raise KnowledgeError("trace_source_mismatch")
                self.span(span)
        return trace

    def question(self, ref):
        self.scope_of(ref)
        record = self.research.question(ref, self.budget)
        if record.reference != ref:
            raise KnowledgeError("question_binding_mismatch")
        self.artifact(record.applicability)
        return record

    def need(self, ref):
        self.scope_of(ref)
        record = self.research.need(ref, self.budget)
        if record.reference != ref:
            raise KnowledgeError("need_binding_mismatch")
        self.scope_of(record.question)
        self.artifact(record.required_context)
        return record
