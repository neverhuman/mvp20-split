"""Immutable observation identity; referenced source claims remain untrusted until resolution."""
from dataclasses import dataclass

from amphora_contracts_core import Identifier, Scope
from pydantic import TypeAdapter, ValidationError

IDENTIFIER = TypeAdapter(Identifier)


class ObservationError(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise ObservationError(reason)


def identifier(value):
    try:
        IDENTIFIER.validate_python(value, strict=True)
    except ValidationError as error:
        raise ObservationError("invalid_observation_identifier") from error


@dataclass(frozen=True, slots=True)
class ObservationReference:
    scope: Scope
    observation_id: str
    revision: int

    def __post_init__(self):
        require(type(self.scope) is Scope,"observation_scope_required")
        identifier(self.observation_id)
        require(type(self.revision) is int and 1 <= self.revision <= 9007199254740991,"observation_revision_bound")


@dataclass(frozen=True, slots=True)
class ObservationIdentity:
    reference: ObservationReference
    supersedes: ObservationReference | None

    def __post_init__(self):
        require(type(self.reference) is ObservationReference,"observation_reference_required")
        prior = self.supersedes
        if prior is None:
            require(self.reference.revision == 1,"observation_predecessor_required")
        else:
            require(type(prior) is ObservationReference,"observation_predecessor_type")
            require(prior.scope == self.reference.scope and prior.observation_id == self.reference.observation_id
                    and prior.revision + 1 == self.reference.revision,"observation_predecessor_mismatch")
