"""Ordered processing with explicit proposed/reported-observed posture and attribution."""
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef, SchemaRef

from ..observations import Quantity
from .validation import bounded_tuple, identifier, require


@dataclass(frozen=True, slots=True)
class Condition:
    name: str
    quantity: Quantity

    def __post_init__(self):
        identifier(self.name)
        require(type(self.quantity) is Quantity,"condition_quantity_required")


@dataclass(frozen=True, slots=True)
class ProcessingContext:
    method: SchemaRef
    conditions: tuple[Condition, ...]
    duration: Quantity | None
    atmosphere: str | None

    def __post_init__(self):
        require(type(self.method) is SchemaRef,"processing_method_required")
        bounded_tuple(self.conditions,64,"condition_bound")
        require(all(type(item) is Condition for item in self.conditions),"condition_required")
        require(len({item.name for item in self.conditions}) == len(self.conditions),"duplicate_condition")
        if self.duration is not None:
            require(type(self.duration) is Quantity,"duration_quantity_required")
            require(self.duration.value.amount >= 0,"negative_processing_duration")
        if self.atmosphere is not None:
            require(type(self.atmosphere) is str and bool(self.atmosphere.strip()) and len(self.atmosphere) <= 128,
                    "invalid_atmosphere")


@dataclass(frozen=True, slots=True)
class ProcessAttribution:
    basis: str
    actor: str
    equipment: tuple[str, ...] | None
    source: ArtifactRef

    def __post_init__(self):
        require(self.basis in ("proposed","observed"),"invalid_preparation_basis")
        identifier(self.actor)
        require(type(self.source) is ArtifactRef,"processing_source_required")
        if self.equipment is not None:
            bounded_tuple(self.equipment,32,"equipment_bound")
            for item in self.equipment:
                identifier(item)
            require(len(set(self.equipment)) == len(self.equipment),"duplicate_equipment")


@dataclass(frozen=True, slots=True)
class ProcessingEvent:
    event_id: str
    context: ProcessingContext
    attribution: ProcessAttribution

    def __post_init__(self):
        identifier(self.event_id)
        require(type(self.context) is ProcessingContext,"processing_context_required")
        require(type(self.attribution) is ProcessAttribution,"processing_attribution_required")


@dataclass(frozen=True, slots=True)
class PreparationHistory:
    events: tuple[ProcessingEvent, ...]

    def __post_init__(self):
        bounded_tuple(self.events,256,"processing_event_bound")
        require(all(type(item) is ProcessingEvent for item in self.events),"processing_event_required")
        require(len({item.event_id for item in self.events}) == len(self.events),"duplicate_processing_event")

    @property
    def posture(self):
        bases = {item.attribution.basis for item in self.events}
        return "unknown" if not bases else next(iter(bases)) if len(bases) == 1 else "mixed"
