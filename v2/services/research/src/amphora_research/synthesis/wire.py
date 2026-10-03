"""Explicit synthesis document mapping; assessment output comes only from the domain policy."""
from amphora_contracts_research import (
    RouteDecisionRecord,
    RouteEvidenceRecord,
    RouteExecutionCheck,
    RouteOptionRecord,
    RouteProvenanceRecord,
    RouteSearchRecord,
    RouteStepRecord,
    SynthesisAssessment,
    SynthesisContextRecord,
    SynthesisProfile,
)

from ..observations.measurement_wire import quantity_from_wire, quantity_to_wire
from .evidence import RouteEvidence, RouteProvenance, RouteStep, SearchRecord, SynthesisContext
from .policy import ExecutionCheck, RouteOption, SynthesisPolicy


def context_to_wire(value):
    return SynthesisContextRecord(candidate=value.candidate,domain=value.domain,purpose=value.purpose,conditions=value.conditions,
                                  scale=None if value.scale is None else quantity_to_wire(value.scale),purity=value.purity)


def context_from_wire(record):
    return SynthesisContext(record.candidate,record.domain,record.purpose,record.conditions,
                            None if record.scale is None else quantity_from_wire(record.scale),record.purity)


def evidence_to_wire(value):
    return RouteEvidenceRecord(context=context_to_wire(value.context),route=value.route,posture=value.posture,
        provenance=RouteProvenanceRecord(method=value.provenance.method,tool=value.provenance.tool,
                                         models=value.provenance.models,sources=value.provenance.sources),
        steps=tuple(RouteStepRecord(step_id=item.step_id,requires=item.requires,posture=item.posture,record=item.record,
                                   sources=item.sources,gaps=item.gaps) for item in value.steps),
        search=None if value.search is None else RouteSearchRecord(scope=value.search.scope,budget=quantity_to_wire(value.search.budget)),
        next_checks=value.next_checks)


def evidence_from_wire(record):
    return RouteEvidence(context_from_wire(record.context),record.route,record.posture,
        RouteProvenance(record.provenance.method,record.provenance.tool,record.provenance.models,record.provenance.sources),
        tuple(RouteStep(item.step_id,item.requires,item.posture,item.record,item.sources,item.gaps) for item in record.steps),
        None if record.search is None else SearchRecord(record.search.scope,quantity_from_wire(record.search.budget)),record.next_checks)


def option_to_wire(value):
    return RouteOptionRecord(evidence=evidence_to_wire(value.evidence),
        checks=tuple(RouteExecutionCheck(criterion_id=item.criterion_id,disposition=item.disposition,evidence=item.evidence,
                                        reasons=item.reasons) for item in value.checks))


def option_from_wire(record):
    return RouteOption(evidence_from_wire(record.evidence),
        tuple(ExecutionCheck(item.criterion_id,item.disposition,item.evidence,item.reasons) for item in record.checks))


def profile_to_wire(policy):
    return SynthesisProfile(wire_version="1",authority=policy.authority,reference=policy.reference,
        context=context_to_wire(policy.context),allowed_postures=policy.allowed_postures,
        allowed_step_postures=policy.allowed_step_postures,required_checks=policy.required_checks)


def profile_from_wire(record):
    return SynthesisPolicy(record.reference,context_from_wire(record.context),record.allowed_postures,
                           record.allowed_step_postures,record.required_checks)


def assess_to_wire(policy, options):
    decisions = policy.assess_alternatives(options)
    return SynthesisAssessment(wire_version="1",authority=policy.authority,policy=profile_to_wire(policy),
        alternatives=tuple(RouteDecisionRecord(option=option_to_wire(item.option),disposition=item.disposition,
                                               blockers=item.blockers,gaps=item.gaps) for item in decisions))
