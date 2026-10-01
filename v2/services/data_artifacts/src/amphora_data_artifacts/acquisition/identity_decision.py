"""Identity observation policy; successful identity never promotes evidence."""

from dataclasses import dataclass

from amphora_contracts_evidence import SourceIdentityObservation
from amphora_contracts_research import IdentityResolution

from .research import ResearchLookupError, lab_identity_query


@dataclass(frozen=True)
class IdentityDecision:
    kind: str
    resolution: IdentityResolution | None

    @classmethod
    def evaluate(cls, prepared, client):
        if prepared.converter_id == "utf8-document":
            return cls("not_applicable", None)
        query = lab_identity_query(prepared)
        if query is None:
            return cls("unresolved", None)
        if client is None:
            raise ResearchLookupError("research_not_configured")
        result = client.resolve(query)
        if (result.scope != query.scope or result.candidate != query.candidate or result.sample != query.sample
                or (result.disposition == "matched") != (result.reason == "exact_identity_only")):
            raise ResearchLookupError("research_binding_mismatch")
        return cls("research_identity", result)

    def record(self, request):
        return SourceIdentityObservation(wire_version="1", request=request, kind=self.kind,
                                         resolution=self.resolution, scientific_authority="none")
