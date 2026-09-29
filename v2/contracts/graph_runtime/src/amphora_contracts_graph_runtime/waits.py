"""Issuer evidence and pinned expectations; these DTOs grant no execution authority."""

from typing import Annotated, Literal

from amphora_contracts_campaigns import ArtifactConstant, ArtifactType
from amphora_contracts_core import ArtifactRef, Digest, Identifier, SafePositiveInt, Scope, WireModel
from pydantic import Field

from .models import GraphNodeView, GraphRunPage


class AcceptedEvidence(WireModel):
    status: Literal["accepted"]
    output: ArtifactConstant


class RejectedEvidence(WireModel):
    status: Literal["rejected"]
    reason_code: Identifier


class AbstainedEvidence(WireModel):
    status: Literal["abstained"]
    reason_code: Identifier


class SupersededEvidence(WireModel):
    status: Literal["superseded"]
    replacement_revision: Identifier
    reason_code: Identifier


class DomainReceipt(WireModel):
    schema_version: Literal["1"] = "1"
    issuer_id: Identifier
    receipt_id: Identifier
    scope: Scope
    purpose: Identifier
    revision: Identifier
    subject: ArtifactRef
    outcome: Annotated[AcceptedEvidence | RejectedEvidence | AbstainedEvidence | SupersededEvidence,
                       Field(discriminator="status")]


class WaitExpectation(WireModel):
    schema_version: Literal["1"] = "1"
    scope: Scope
    run_id: Identifier
    activation_id: Digest
    plan_sha256: Digest
    wait_revision: SafePositiveInt
    issuer_id: Identifier
    purpose: Identifier
    expected_revision: Identifier
    subject: ArtifactRef
    output_type: ArtifactType
    # UTC microseconds preserve command-v1's exact integer encoding and database ordering.
    deadline_us: Annotated[int, Field(ge=0, le=9007199254740991)]
    on_timeout: Literal["blocked", "abstained"]


class SubmitDomainReceipt(WireModel):
    schema_version: Literal["1"] = "1"
    run_id: Identifier
    activation_id: Digest
    wait_revision: SafePositiveInt
    expectation_sha256: Digest
    receipt: DomainReceipt


class AcceptedDomainReceipt(DomainReceipt):
    outcome: AcceptedEvidence


class WaitAccepted(WireModel):
    status: Literal["accepted"]
    receipt: AcceptedDomainReceipt


class WaitUnfulfilled(WireModel):
    status: Literal["abstained", "blocked", "cancelled"]
    reason_code: Identifier
    receipt: DomainReceipt | None = None


class WaitClosure(WireModel):
    schema_version: Literal["1"] = "1"
    scope: Scope
    run_id: Identifier
    activation_id: Digest
    wait_revision: SafePositiveInt
    expectation_sha256: Digest
    closure_revision: SafePositiveInt
    outcome: Annotated[WaitAccepted | WaitUnfulfilled, Field(discriminator="status")]


class WaitObservation(WireModel):
    schema_version: Literal["1"] = "1"
    expectation: WaitExpectation
    expectation_sha256: Digest
    closure: WaitClosure | None


class GraphNodeViewV2(GraphNodeView):
    kind: Literal["invoke", "branch", "join", "scatter", "iterate", "finish", "await"]


class GraphRunPageV2(GraphRunPage):
    schema_version: Literal["2"] = "2"
    nodes: Annotated[tuple[GraphNodeViewV2, ...], Field(max_length=100)]
