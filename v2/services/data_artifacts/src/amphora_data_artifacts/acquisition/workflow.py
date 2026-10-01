"""Owner-local ingestion stages over authorized, finalized artifact bytes."""

from amphora_contracts_core import ArtifactRef
from amphora_contracts_evidence import SourceRevision

from .adapters import prepare_document, prepare_lab
from .identity_decision import IdentityDecision
from .observations import IdentityObservations
from .provenance import ProvenanceError, SourceDocument


class AcquisitionWorkflow:
    """Replayable stages; publication remains the existing artifact owner's operation.

    No caller-supplied preparation is trusted at retention. Recompute it from the
    authorized raw artifact and compare the actual finalized output before storing
    a trace. Rights references are provenance, not a current-use authorization.
    """

    def __init__(self, reads, ledger, research=None):
        self.reads = reads
        self.ledger = ledger
        self.rights = ledger.rights
        self.observations = IdentityObservations(ledger.engine)
        self.research = research

    def _content(self, principal, reference: ArtifactRef):
        if reference.scope != principal.scope:
            raise ProvenanceError("artifact_scope_mismatch")
        stored, content = self.reads.content(principal, reference.artifact_id)
        if stored.reference != reference:
            raise ProvenanceError("catalog_reference_mismatch")
        return content

    def prepare(self, principal, revision: SourceRevision):
        principal.require("acquire")
        if revision.reference.scope != principal.scope or revision.rights.scope != principal.scope:
            raise ProvenanceError("source_scope_mismatch")
        snapshot = self.rights.capture(principal, (revision.reference.raw.artifact_id,), (revision.rights,), "process")
        source = SourceDocument(revision.reference, self._content(principal, revision.reference.raw))
        # Register before conversion: a failed parser must not erase delivery
        # identity or allow different bytes to be silently retried under its key.
        self.ledger.register(principal, revision, source)
        prepared = prepare_document(source) if revision.method.format == "utf8_document" else prepare_lab(source)
        self.rights.recheck(principal, snapshot)
        return prepared

    def retain(self, principal, revision: SourceRevision, trace_id: str, output: ArtifactRef):
        principal.require("acquire")
        principal.require("read")
        snapshot = self.rights.capture(principal, (revision.reference.raw.artifact_id, output.artifact_id),
                                      (revision.rights,), "process")
        prepared = self.prepare(principal, revision)
        content = self._content(principal, output)
        if content != prepared.content:
            raise ProvenanceError("prepared_output_mismatch")
        verified = prepared.trace(trace_id, output)
        return self.ledger.retain_trace(principal, verified.trace, prepared.source, content, rights_snapshot=snapshot)

    def observe(self, principal, request):
        principal.require("acquire")
        principal.require("read")
        existing = self.observations.begin(principal, request)
        if existing is not None:
            return existing
        trace, source = self.observations.source(principal, request)
        snapshot = self.rights.capture(principal, (trace.source.raw.artifact_id, trace.output.artifact_id),
                                      (source.rights,), "process")
        prepared = self.prepare(principal, source)
        if (prepared.trace(trace.trace_id, trace.output).reference() != request.trace
                or self._content(principal, trace.output) != prepared.content):
            raise ProvenanceError("observation_conversion_mismatch")
        decision = IdentityDecision.evaluate(prepared, self.research)
        return self.observations.complete(principal, decision.record(request), rights_snapshot=snapshot)
