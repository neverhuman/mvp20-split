"""Receipt storage, structural compilation and execution admission are distinct."""

from dataclasses import dataclass

from amphora_contracts_graph_runtime import (
    DraftCommandReceipt,
    DraftRevision,
    DraftValidation,
)

from ..context.policy import require
from .request import AuthoringRequest


@dataclass(frozen=True)
class AuthoringOutcome:
    request: AuthoringRequest
    receipt: DraftCommandReceipt
    readback: DraftRevision | DraftValidation | None
    status: str

    @classmethod
    def bind(cls, request, receipt, readback=None):
        command = request.command()
        receipt = DraftCommandReceipt.model_validate_json(receipt.model_dump_json())
        outcome = receipt.outcome
        require(outcome.binding.identity == command.identity and outcome.binding.request_sha256 == command.sha256,
                'authoring_receipt_binding')
        if outcome.status != 'accepted':
            require(readback is None, 'authoring_unaccepted_readback')
            return cls(request, receipt, None, outcome.status)
        payload = request.payload()
        saving = command.identity.command_family == 'definition.save'
        commit = outcome.committed
        require(commit.kind == ('draft_revision' if saving else 'draft_validation'), 'authoring_commit_kind')
        require(commit.revision == (payload.expected_revision + 1 if saving else payload.revision), 'authoring_commit_revision')
        if saving:
            require(commit.object_id == payload.draft_id, 'authoring_commit_identity')
        else:
            require(commit.content_sha256 == payload.content_sha256, 'authoring_commit_content')
        if readback is None:
            return cls(request, receipt, None, 'awaiting_readback')
        model = DraftRevision if saving else DraftValidation
        readback = model.model_validate_json(readback.model_dump_json())
        require(readback.scope == command.identity.scope, 'authoring_readback_scope')
        if saving:
            head = readback.head
            require(head.draft_id == commit.object_id and head.revision == commit.revision and
                    head.content_sha256 == commit.content_sha256, 'authoring_readback_commit')
            require(head.title == payload.title and readback.definition == payload.definition and
                    readback.parent_revision == payload.expected_revision, 'authoring_saved_content')
            status = 'saved'
        else:
            require(readback.validation_id == commit.object_id and readback.revision == commit.revision and
                    readback.content_sha256 == commit.content_sha256 and readback.draft_id == payload.draft_id,
                    'authoring_readback_commit')
            status = 'compiled' if readback.structurally_valid else 'structural_invalid'
        return cls(request, receipt, readback, status)
