"""Collect exact public inputs and reject foreign or equivocal identities before I/O."""

from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef, Scope, WireModel
from amphora_contracts_evidence import ConversionTraceRef, SourceRevisionRef, SourceSpan
from amphora_contracts_knowledge import DomainGraphRef
from amphora_contracts_research import EvidenceNeedRef, ResearchQuestionRef

from .canonical import KnowledgeError


@dataclass(frozen=True)
class ReferencedInputs:
    artifacts: tuple[ArtifactRef, ...]
    sources: tuple[SourceRevisionRef, ...]
    traces: tuple[ConversionTraceRef, ...]
    questions: tuple[ResearchQuestionRef, ...]
    needs: tuple[EvidenceNeedRef, ...]
    spans: tuple[SourceSpan, ...]

    @classmethod
    def collect(cls, proposal):
        buckets = {kind: {} for kind in ("artifacts", "sources", "traces", "questions", "needs", "spans")}

        def retain(kind, key, value):
            previous = buckets[kind].get(key)
            if previous is not None and previous != value:
                raise KnowledgeError("reference_identity_conflict")
            buckets[kind][key] = value
            if len(buckets[kind]) > (8192 if kind == "spans" else 128):
                raise KnowledgeError("reference_limit")

        def visit(value):
            if isinstance(value, Scope) and value != proposal.graph.scope:
                raise KnowledgeError("reference_scope_mismatch")
            if (isinstance(value, WireModel) and "scope" in type(value).model_fields
                    and value.scope != proposal.graph.scope):
                raise KnowledgeError("reference_scope_mismatch")
            if isinstance(value, DomainGraphRef) and value != proposal.graph:
                raise KnowledgeError("reference_graph_mismatch")
            if isinstance(value, ArtifactRef):
                retain("artifacts", value.artifact_id, value)
            elif isinstance(value, SourceRevisionRef):
                retain("sources", (value.source_id, value.revision_id), value)
            elif isinstance(value, ConversionTraceRef):
                retain("traces", value.trace_id, value)
            elif isinstance(value, ResearchQuestionRef):
                retain("questions", (value.question_id, value.revision), value)
            elif isinstance(value, EvidenceNeedRef):
                retain("needs", (value.need_id, value.revision), value)
            elif isinstance(value, SourceSpan):
                if not 0 <= value.start <= value.end <= value.source.raw.size_bytes:
                    raise KnowledgeError("source_span_bounds")
                retain("spans", (value.source.source_id, value.source.revision_id, value.start, value.end), value)
            if isinstance(value, WireModel):
                for name in type(value).model_fields:
                    visit(getattr(value, name))
            elif isinstance(value, tuple):
                for item in value:
                    visit(item)

        visit(proposal)
        values = {kind: tuple(bucket[key] for key in sorted(bucket)) for kind, bucket in buckets.items()}
        return cls(values["artifacts"], values["sources"], values["traces"], values["questions"], values["needs"], values["spans"])
