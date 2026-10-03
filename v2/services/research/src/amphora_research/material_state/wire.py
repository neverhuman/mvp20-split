"""Explicit material mapping retains original ordered evidence and reruns domain invariants."""
from amphora_contracts_research import (
    MaterialFeatureEvidence,
    MaterialFeatureRecord,
    MaterialStateRevision,
    ProcessingAttribution,
    ProcessingCondition,
    ProcessingContextRecord,
    ProcessingEventRecord,
)

from ..observations import measurement_wire
from .features import FeatureEvidence, MaterialFeature
from .preparation import Condition, PreparationHistory, ProcessAttribution, ProcessingContext, ProcessingEvent
from .state import MaterialState, StateIdentity


def event_to_wire(event):
    context, attribution = event.context,event.attribution
    return ProcessingEventRecord(event_id=event.event_id,
        context=ProcessingContextRecord(method=context.method,
            conditions=tuple(ProcessingCondition(name=c.name,quantity=measurement_wire.quantity_to_wire(c.quantity)) for c in context.conditions),
            duration=None if context.duration is None else measurement_wire.quantity_to_wire(context.duration),atmosphere=context.atmosphere),
        attribution=ProcessingAttribution(basis=attribution.basis,actor=attribution.actor,
                                         equipment=attribution.equipment,source=attribution.source))


def event_from_wire(record):
    context, attribution = record.context,record.attribution
    return ProcessingEvent(record.event_id,ProcessingContext(context.method,
        tuple(Condition(c.name,measurement_wire.quantity_from_wire(c.quantity)) for c in context.conditions),
        None if context.duration is None else measurement_wire.quantity_from_wire(context.duration),context.atmosphere),
        ProcessAttribution(attribution.basis,attribution.actor,attribution.equipment,attribution.source))


def to_wire(state):
    return MaterialStateRevision(wire_version="1",reference=state.identity.reference,candidate=state.identity.candidate,
        supersedes=state.identity.supersedes,preparation=tuple(event_to_wire(item) for item in state.preparation.events),
        features=tuple(MaterialFeatureRecord(name=item.name,value=measurement_wire.to_wire(item.value),
            evidence=MaterialFeatureEvidence(basis=item.evidence.basis,method=item.evidence.method,source=item.evidence.source)) for item in state.features))


def from_wire(record):
    return MaterialState(StateIdentity(record.reference,record.candidate,record.supersedes),
        PreparationHistory(tuple(event_from_wire(item) for item in record.preparation)),
        tuple(MaterialFeature(item.name,measurement_wire.from_wire(item.value),
            FeatureEvidence(item.evidence.basis,item.evidence.method,item.evidence.source)) for item in record.features))
