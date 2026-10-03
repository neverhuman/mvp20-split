"""Reconciliation output is projected from the report aggregate, never producer verdicts."""
from amphora_contracts_research import LabReportResolution, ObservationMatchRecord

from .wire import reference_to_wire, to_wire


def to_resolution(report):
    return LabReportResolution(wire_version="1",authority="synthetic",source=report.source,raw_report=report.raw_report,
        profile=report.configured.document,disposition=report.disposition,
        observations=tuple(to_wire(item.observation) for item in report.entries),
        matches=tuple(ObservationMatchRecord(observation=reference_to_wire(item.observation.identity.reference),
            disposition=item.match.disposition,reasons=item.match.reasons,state_known=item.match.state_known) for item in report.entries),
        missing_expectations=report.missing_expectations,unavailable_values=tuple(reference_to_wire(ref) for ref in report.unavailable_values))
