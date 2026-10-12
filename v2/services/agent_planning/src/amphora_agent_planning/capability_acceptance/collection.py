"""One bounded public Registry read and bounded current Data processing, outside SQL."""
from dataclasses import dataclass

from ..metadata_reads import MetadataWindow
from ..source_access.budget import ReadBudget
from ..registry_access import ObservedRelease
from .review import AcceptanceReview, ProcessedEvidence, accepted, select_report


@dataclass(frozen=True)
class AcceptanceCollector:
    registry: object
    data: object

    def collect(self, capability, specification):
        accepted(specification.request == capability.reference, 'capability_acceptance_request')
        select_report(specification.acceptance_evidence)
        for reference in specification.acceptance_evidence:
            accepted(reference.scope == capability.curation.scope and reference.size_bytes <= 4194304,
                'capability_evidence_bound')
        window = MetadataWindow('registry', seconds=10)
        release = self.registry.read('/v1/releases/' + specification.release.descriptor_sha256, window)
        window.remaining()
        ObservedRelease.bind(release, capability.curation.scope, specification.release)
        accepted(release.status in {'registered', 'active'}, 'capability_release_unavailable')
        budget = ReadBudget(seconds=20, max_calls=32, max_bytes=16777216)
        evidence = []
        for reference in specification.acceptance_evidence:
            metadata = self.data.artifact(reference, budget)
            accepted(reference == metadata, 'capability_evidence_identity')
            evidence.append(ProcessedEvidence.bind(reference, metadata, self.data.content(reference, budget)))
        budget.remaining_total()
        return AcceptanceReview.bind(capability, specification, release, tuple(evidence))
