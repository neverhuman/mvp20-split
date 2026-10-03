"""Reference-only selection and synthetic publication outcome; Runtime still owns acceptance."""

from typing import Annotated, Literal

from amphora_contracts_artifacts import DerivationReceipt
from amphora_contracts_core import Identifier, Scope, WireModel
from amphora_contracts_graph_runtime import DomainReceipt
from pydantic import Field


class AssessmentPublicationRequest(WireModel):
    wire_version: Literal["1"]
    scope: Scope
    assessment_id: Identifier


class AssessmentPublicationPending(WireModel):
    status: Literal["pending"]


class AssessmentPublicationFailed(WireModel):
    status: Literal["failed"]
    code: Identifier
    external_effects: Literal["possible"]


class AssessmentPublished(WireModel):
    status: Literal["published"]
    derivation: DerivationReceipt
    receipt: DomainReceipt


class AssessmentPublicationStatus(WireModel):
    wire_version: Literal["1"]
    request: AssessmentPublicationRequest
    actor_id: Identifier
    outcome: Annotated[AssessmentPublicationPending | AssessmentPublicationFailed | AssessmentPublished,
                       Field(discriminator="status")]
