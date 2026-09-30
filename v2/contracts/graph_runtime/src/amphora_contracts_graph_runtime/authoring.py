"""Draft interchange only; revision transitions and validation authority belong to Runtime."""

import json
from typing import Annotated, Literal

from amphora_contracts_campaigns import ExecutableCampaignV4
from amphora_contracts_commands import CanonicalCommand, CommandEncodingError, CommandIdentity
from amphora_contracts_core import Digest, Finding, Identifier, SafePositiveInt, Scope, WireModel
from pydantic import Field, model_validator


class SaveDraft(WireModel):
    schema_version: Literal["1"] = "1"
    draft_id: Identifier
    expected_revision: Annotated[int, Field(ge=0, le=9007199254740991)]
    title: Annotated[str, Field(min_length=1, max_length=128)]
    definition: ExecutableCampaignV4


class ValidateDraft(WireModel):
    schema_version: Literal["1"] = "1"
    draft_id: Identifier
    revision: SafePositiveInt
    content_sha256: Digest


class DraftHead(WireModel):
    draft_id: Identifier
    revision: SafePositiveInt
    content_sha256: Digest
    title: Annotated[str, Field(min_length=1, max_length=128)]


class DraftRevision(WireModel):
    schema_version: Literal["1"] = "1"
    scope: Scope
    head: DraftHead
    parent_revision: Annotated[int, Field(ge=0, le=9007199254740991)]
    definition: ExecutableCampaignV4

    @model_validator(mode="after")
    def consistent_identity(self):
        if self.scope != self.definition.scope or self.parent_revision != self.head.revision - 1:
            raise ValueError("inconsistent_draft_identity")
        return self


class DraftPage(WireModel):
    schema_version: Literal["1"] = "1"
    scope: Scope
    drafts: Annotated[tuple[DraftHead, ...], Field(max_length=50)]
    next_after: Identifier | None


class DraftValidation(WireModel):
    schema_version: Literal["1"] = "1"
    scope: Scope
    validation_id: Identifier
    draft_id: Identifier
    revision: SafePositiveInt
    content_sha256: Digest
    universe_sha256: Digest
    structurally_valid: bool
    plan_sha256: Digest | None
    findings: Annotated[tuple[Finding, ...], Field(max_length=20)]
    pending_checks: Annotated[tuple[Identifier, ...], Field(max_length=16)]
    scientific_acceptance: Literal["not_established"] = "not_established"

    @model_validator(mode="after")
    def consistent_plan(self):
        if self.structurally_valid != (self.plan_sha256 is not None):
            raise ValueError("inconsistent_validation_plan")
        return self


class DraftReceiptBinding(WireModel):
    identity: CommandIdentity
    request_sha256: Digest
    operation_id: Identifier


class DraftCommit(WireModel):
    kind: Literal["draft_revision", "draft_validation"]
    object_id: Identifier
    revision: SafePositiveInt
    content_sha256: Digest


class DraftAccepted(WireModel):
    status: Literal["accepted"]
    binding: DraftReceiptBinding
    committed: DraftCommit


class DraftRejected(WireModel):
    status: Literal["rejected"]
    binding: DraftReceiptBinding
    reason_code: Identifier


class DraftPending(WireModel):
    status: Literal["pending"]
    binding: DraftReceiptBinding


class DraftCommandReceipt(WireModel):
    schema_version: Literal["1"] = "1"
    outcome: Annotated[DraftAccepted | DraftRejected | DraftPending, Field(discriminator="status")]


def parse_authoring_command(family, raw):
    try:
        model = {"definition.save": SaveDraft, "definition.validate": ValidateDraft}[family]
    except KeyError as error:
        raise CommandEncodingError("unknown_family") from error
    command = CanonicalCommand.for_family(raw, family, model, allow_numeric=family == "definition.save")
    if family == "definition.save":
        payload = json.loads(command.canonical_bytes)["payload"]
        if payload["definition"]["scope"] != command.identity.scope.model_dump():
            raise CommandEncodingError("scope_mismatch")
    return command
