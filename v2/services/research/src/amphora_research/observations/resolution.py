"""One bounded authenticated Data resolution attempt; no network while holding owner transactions."""
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef
from amphora_contracts_research import SyntheticLabReport, synthetic_lab_report_schema

from ..assessment.resolution import payload, require_inputs
from ..experiments.wire import from_wire as experiment_from_wire
from .identity import require
from .reports import ConfiguredLabReturn, ReconciledReport


@dataclass(frozen=True, slots=True)
class ResolvedLabReport:
    report: ReconciledReport
    inputs: tuple[ArtifactRef, ...]


class LabReportResolver:
    def __init__(self, experiments, reader):
        self.experiments,self.reader = experiments,reader

    def resolve(self, configured, source):
        require(type(configured) is ConfiguredLabReturn,"lab_profile_required")
        require(type(source) is ArtifactRef,"lab_report_source_required")
        profile = configured.document
        scope = profile.experiment.scope
        require(self.reader.scope == scope and source.scope == scope,"lab_report_scope_mismatch")
        require(source.schema_ref == synthetic_lab_report_schema() and source.media_type == "application/json","lab_report_schema_mismatch")
        require(source.size_bytes <= 8*1024*1024,"lab_report_byte_limit")
        declaration = self.experiments.read(scope,profile.experiment)
        require(declaration is not None,"unknown_lab_experiment")
        experiment = experiment_from_wire(declaration)
        content, proof = self.reader.published(source,frozenset(profile.publishers))
        report = payload(SyntheticLabReport,content)
        require(report.issuer == proof.origin.actor_id,"lab_report_issuer_mismatch")
        method = proof.declaration.transformation
        require((method.transformation_id,method.version,method.sha256) ==
                (profile.adapter.schema_id,profile.adapter.version,profile.adapter.sha256),"lab_report_method_mismatch")
        required = (report.raw_report,experiment.protocol.applicability,experiment.protocol.source)
        require_inputs(proof,required)
        # Recheck current source access, exact bytes and context before accepting a newly resolved report.
        for reference in required:
            self.reader.read(reference)
        return ResolvedLabReport(ReconciledReport.reconcile(configured,experiment,source,report),self.reader.consumed)
