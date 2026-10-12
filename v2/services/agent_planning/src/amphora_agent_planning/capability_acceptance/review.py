"""Mechanical compatibility plus explicit owner endorsement, not inferred science."""
from dataclasses import dataclass
import hashlib
import json

from amphora_contracts_core import ArtifactRef

from ..context.snapshot import _object, _constant
from ..registry_access import ObservedRelease
from .wire import AcceptanceRecord, acceptance_schema


class AcceptanceRejected(ValueError):
    """A bounded known evidence mismatch; not a transport or persistence failure."""


def accepted(condition, reason):
    if not condition:
        raise AcceptanceRejected(reason)


def select_report(references):
    reports = tuple(ref for ref in references if ref.schema_ref == acceptance_schema())
    accepted(len(reports) == 1 and reports[0].media_type == 'application/json', 'capability_acceptance_report_required')
    accepted(0 < reports[0].size_bytes <= 65536, 'capability_acceptance_size')
    return reports[0]


@dataclass(frozen=True)
class ProcessedEvidence:
    reference: ArtifactRef
    body: bytes

    @classmethod
    def bind(cls, reference, metadata, body):
        accepted(reference == metadata, 'capability_evidence_identity')
        accepted(type(body) is bytes and len(body) == reference.size_bytes
            and hashlib.sha256(body).hexdigest() == reference.sha256, 'capability_evidence_content')
        return cls(reference, body)


@dataclass(frozen=True)
class AcceptanceReport:
    canonical: bytes

    @classmethod
    def parse(cls, body):
        accepted(type(body) is bytes and 0 < len(body) <= 65536, 'capability_acceptance_size')
        try:
            value = json.loads(body.decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
            record = AcceptanceRecord.model_validate_json(json.dumps(value, allow_nan=False))
        except (ValueError, UnicodeError, RecursionError) as error:
            raise AcceptanceRejected('capability_acceptance_invalid') from error
        return cls(json.dumps(record.model_dump(mode='json'), sort_keys=True, separators=(',', ':'),
            ensure_ascii=False, allow_nan=False).encode('utf-8'))

    def document(self):
        return AcceptanceRecord.model_validate_json(self.canonical)


@dataclass(frozen=True)
class AcceptanceReview:
    release: ObservedRelease
    report: AcceptanceReport
    report_reference: ArtifactRef
    evidence: tuple[ProcessedEvidence, ...]

    @classmethod
    def bind(cls, capability, specification, release, evidence):
        accepted(specification.request == capability.reference, 'capability_acceptance_request')
        # Reconstruct the whole descriptor digest and lock, not a caller-supplied status flag.
        observed = ObservedRelease.bind(release, capability.curation.scope, specification.release)
        accepted(release.status in {'registered', 'active'}, 'capability_release_unavailable')
        expected = specification.acceptance_evidence
        accepted(type(evidence) is tuple and tuple(row.reference for row in evidence) == expected,
            'capability_evidence_coverage')
        accepted(len({ref.artifact_id for ref in expected}) == len(expected)
            and all(ref.scope == capability.curation.scope for ref in expected), 'capability_evidence_scope')
        for row in evidence:
            ProcessedEvidence.bind(row.reference, row.reference, row.body)
        selected = select_report(expected)
        captured = next(row for row in evidence if row.reference == selected)
        observed, report, selected = cls.review_report(capability, specification, release, captured.body)
        return cls(observed, report, selected, evidence)

    @classmethod
    def review_report(cls, capability, specification, release, body):
        """Replay report semantics; this alone does not attest Data processing."""
        accepted(specification.request == capability.reference, 'capability_acceptance_request')
        observed = ObservedRelease.bind(release, capability.curation.scope, specification.release)
        accepted(release.status in {'registered', 'active'}, 'capability_release_unavailable')
        expected = specification.acceptance_evidence
        accepted(len({ref.artifact_id for ref in expected}) == len(expected)
            and all(ref.scope == capability.curation.scope for ref in expected), 'capability_evidence_scope')
        selected = select_report(expected)
        ProcessedEvidence.bind(selected, selected, body)
        report = AcceptanceReport.parse(body)
        record, gap = report.document(), capability.gap
        accepted(record.request == capability.reference and record.proposal_sha256 == capability.proposal_sha256
            and record.gap_key == gap.gap_key and record.release == specification.release, 'capability_acceptance_binding')
        tool = release.descriptor.tool
        accepted(record.requested_applicability == gap.applicability
            and len(set(record.descriptor_applicability)) == len(record.descriptor_applicability)
            and set(record.descriptor_applicability) <= set(tool.applicability), 'capability_acceptance_applicability')
        cls._ports(gap.inputs, tool.inputs, inputs=True)
        cls._ports(gap.outputs, tool.outputs, inputs=False)
        accepted(tuple(row.index for row in record.criteria) == tuple(range(len(gap.acceptance_criteria))),
            'capability_acceptance_criteria_coverage')
        supporting = set(expected) - {selected}
        for row, criterion in zip(record.criteria, gap.acceptance_criteria, strict=True):
            accepted(row.criterion == criterion, 'capability_acceptance_criterion')
            accepted(row.result == 'passed', 'capability_acceptance_unproven')
            accepted(len(set(row.supporting_artifacts)) == len(row.supporting_artifacts)
                and set(row.supporting_artifacts) <= supporting, 'capability_acceptance_support')
        return observed, report, selected

    @staticmethod
    def _ports(requested, offered, *, inputs):
        ports = {port.name: port for port in offered}
        names = {port.name for port in requested}
        accepted(len(names) == len(requested) and names <= set(ports), 'capability_acceptance_ports')
        if inputs:
            accepted({port.name for port in offered if port.required} <= names, 'capability_acceptance_required_input')
        for request in requested:
            port = ports[request.name]
            accepted(request.representation == port.representation
                and (request.schema_ref is None or request.schema_ref == port.schema_ref)
                and (request.unit is None or request.unit == port.unit), 'capability_acceptance_port_type')
