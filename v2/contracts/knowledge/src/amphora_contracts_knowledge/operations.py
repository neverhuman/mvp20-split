"""Closed bounded edit vocabulary; operations carry no execution authority."""

from typing import Annotated, Literal

from amphora_contracts_core import WireModel
from pydantic import Field

from .records import DomainAssertion, DomainEntity
from .references import AssertionRevisionRef, EntityRevisionRef


class AddEntity(WireModel):
    operation: Literal["add_entity"]
    entity: DomainEntity


class AddAssertion(WireModel):
    operation: Literal["add_assertion"]
    assertion: DomainAssertion


class CorrectAssertion(WireModel):
    operation: Literal["correct_assertion"]
    prior: AssertionRevisionRef
    replacement: DomainAssertion


class RetractAssertion(WireModel):
    operation: Literal["retract_assertion"]
    assertion: AssertionRevisionRef


class MergeEntities(WireModel):
    operation: Literal["merge_entities"]
    source: EntityRevisionRef
    target: EntityRevisionRef


class ReviseEntityContext(WireModel):
    operation: Literal["revise_entity_context"]
    prior: EntityRevisionRef
    replacement: DomainEntity


GraphOperation = Annotated[
    AddEntity | AddAssertion | CorrectAssertion | RetractAssertion | MergeEntities | ReviseEntityContext,
    Field(discriminator="operation"),
]
