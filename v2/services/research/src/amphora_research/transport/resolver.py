"""Resolution reads owner history only and cannot publish or accept evidence."""

from amphora_contracts_research import IdentityResolution, ResolveIdentity

from ..identity.samples import CandidateDefinition, IdentityMatch, SampleDefinition


class IdentityResolver:
    def __init__(self, ledger):
        self.ledger = ledger

    def resolve(self, principal, request: ResolveIdentity) -> IdentityResolution:
        principal.require("resolve_identity", request.scope)
        principal.require("resolve_identity", request.candidate.scope)
        principal.require("resolve_identity", request.sample.scope)
        candidate = self.ledger.read(request.scope, "candidate", request.candidate.candidate_id, request.candidate.revision)
        sample = self.ledger.read(request.scope, "sample", request.sample.sample_id, request.sample.revision)
        match = IdentityMatch.reconcile(request.candidate, request.sample,
            None if candidate is None else CandidateDefinition(candidate),
            None if sample is None else SampleDefinition(sample))
        return IdentityResolution(wire_version="1", scope=request.scope, candidate=request.candidate,
            sample=request.sample, disposition=match.disposition, reason=match.reason, authority="identity_only")
