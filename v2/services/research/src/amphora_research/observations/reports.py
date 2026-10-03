"""A report's return coverage is distinct from measured availability and scientific quality."""
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef
from amphora_contracts_research import LabReturnProfile, ObservationRevision, SyntheticLabReport

from ..experiments.model import Experiment
from ..experiments.wire import reference_to_wire
from .identity import ObservationError, require
from .matching import ObservationMatch
from .records import Observation
from .wire import from_wire


@dataclass(frozen=True, slots=True)
class ConfiguredLabReturn:
    document: LabReturnProfile

    def __post_init__(self):
        require(type(self.document) is LabReturnProfile,"lab_profile_required")
        require(len(set(self.document.publishers)) == len(self.document.publishers),"duplicate_lab_publisher")


@dataclass(frozen=True, slots=True)
class MatchedObservation:
    observation: Observation
    match: ObservationMatch


@dataclass(frozen=True, slots=True)
class ReconciledReport:
    configured: ConfiguredLabReturn
    source: ArtifactRef
    raw_report: ArtifactRef
    entries: tuple[MatchedObservation, ...]
    missing_expectations: tuple[str, ...]

    @property
    def disposition(self):
        if not any(item.match.disposition == "matched" for item in self.entries):
            return "unmatched"
        return "partial" if self.missing_expectations else "complete"

    @property
    def unavailable_values(self):
        return tuple(item.observation.identity.reference for item in self.entries if not item.observation.value_available)

    @classmethod
    def reconcile(cls, configured, experiment, source, report):
        require(type(configured) is ConfiguredLabReturn and type(experiment) is Experiment,"lab_reconciliation_context_required")
        require(type(source) is ArtifactRef and type(report) is SyntheticLabReport,"lab_report_required")
        profile = configured.document
        require(reference_to_wire(experiment.identity.reference) == profile.experiment,"lab_experiment_revision_mismatch")
        require(source.scope == profile.experiment.scope and report.raw_report.scope == source.scope,"lab_report_scope_mismatch")
        require(report.adapter == profile.adapter,"lab_adapter_mismatch")
        require(report.issuer in profile.publishers,"lab_issuer_not_configured")
        ids = tuple((row.reference.scope,row.reference.observation_id) for row in report.observations)
        require(len(set(ids)) == len(ids),"duplicate_lab_observation")
        entries = []
        for row in report.observations:
            if row.reference.scope != source.scope:
                raise ObservationError("lab_observation_scope_mismatch")
            # The source is attached after the hash-authorized read, avoiding a self-referential payload hash.
            record = ObservationRevision(wire_version="1",reference=row.reference,supersedes=row.supersedes,source=source,
                binding=row.binding,value=row.value,quality=row.quality)
            observation = from_wire(record)
            entries.append(MatchedObservation(observation,ObservationMatch.reconcile(observation,experiment)))
        returned = {item.observation.binding.target.expectation_id for item in entries if item.match.disposition == "matched"}
        missing = tuple(item.expectation_id for item in experiment.expectations if item.expectation_id not in returned)
        return cls(configured,source,report.raw_report,tuple(entries),missing)
