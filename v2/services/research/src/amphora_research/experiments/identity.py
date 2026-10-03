"""Owner-scoped immutable experiment identity, without persistence or head selection."""
from dataclasses import dataclass

from amphora_contracts_core import Identifier, Scope
from pydantic import TypeAdapter, ValidationError

IDENTIFIER = TypeAdapter(Identifier)


class ExperimentError(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise ExperimentError(reason)


def identifier(value):
    try:
        IDENTIFIER.validate_python(value, strict=True)
    except ValidationError as error:
        raise ExperimentError("invalid_experiment_identifier") from error


@dataclass(frozen=True, slots=True)
class ExperimentReference:
    scope: Scope
    experiment_id: str
    revision: int

    def __post_init__(self):
        require(type(self.scope) is Scope,"experiment_scope_required")
        identifier(self.experiment_id)
        require(type(self.revision) is int and 1 <= self.revision <= 9007199254740991,"experiment_revision_bound")


@dataclass(frozen=True, slots=True)
class ExperimentIdentity:
    reference: ExperimentReference
    supersedes: ExperimentReference | None

    def __post_init__(self):
        require(type(self.reference) is ExperimentReference,"experiment_reference_required")
        prior = self.supersedes
        if prior is None:
            require(self.reference.revision == 1,"experiment_predecessor_required")
        else:
            require(type(prior) is ExperimentReference,"experiment_predecessor_type")
            require(prior.scope == self.reference.scope and prior.experiment_id == self.reference.experiment_id
                    and prior.revision + 1 == self.reference.revision,"experiment_predecessor_mismatch")
