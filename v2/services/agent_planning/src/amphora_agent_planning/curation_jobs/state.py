"""Immutable progress projection; a lease is never evidence of model issuance."""
from dataclasses import dataclass
from datetime import UTC
import hashlib

from amphora_contracts_campaign_curation import CurationView
from ..context.policy import require
from ..curation_intake.record import encoded


@dataclass(frozen=True)
class JobProgress:
    original: object
    view: CurationView

    @classmethod
    def initial(cls, original, at):
        receipt = original.receipt.model_copy(update={
            'revision': 1, 'phase': 'assembling', 'updated_at': at.astimezone(UTC)})
        return cls(original, original.view().model_copy(update={'receipt': receipt}))

    @classmethod
    def restore(cls, original, row):
        raw = bytes(row['view_bytes'])
        view = CurationView.model_validate_json(raw)
        require(encoded(view) == raw and hashlib.sha256(raw).hexdigest() == row['view_sha256'],
                'stored_curation_progress_mismatch')
        first, current = original.receipt, view.receipt
        require(current.identity == first.identity and current.reference == first.reference
                and current.request_sha256 == first.request_sha256
                and current.created_at == first.created_at
                and current.updated_at >= first.created_at
                and current.revision == row['revision'] and current.revision >= 1
                and view.specification == original.incoming.request.payload,
                'stored_curation_progress_mismatch')
        return cls(original, view)

    def prepared(self, at):
        require(self.view.receipt.phase == 'assembling', 'curation_preparation_phase')
        receipt = self.view.receipt.model_copy(update={
            'phase': 'awaiting_provider', 'reason_code': 'context_prepared',
            'revision': self.view.receipt.revision + 1, 'updated_at': at.astimezone(UTC)})
        return JobProgress(self.original, CurationView.model_validate_json(
            self.view.model_copy(update={'receipt': receipt}).model_dump_json()))

    def fail(self, reason, at):
        # An unfinished provider/compiler operation cannot be declared effect-free.
        phase = 'failed' if self.view.receipt.phase == 'assembling' else 'indeterminate'
        require(self.view.receipt.phase not in {'ready', 'failed', 'indeterminate', 'abstained'},
                'curation_job_terminal')
        receipt = self.view.receipt.model_copy(update={
            'phase': phase, 'reason_code': reason, 'revision': self.view.receipt.revision + 1,
            'updated_at': at.astimezone(UTC)})
        view = CurationView.model_validate_json(
            self.view.model_copy(update={'receipt': receipt}).model_dump_json())
        return JobProgress(self.original, view)

    @property
    def terminal(self):
        return self.view.receipt.phase in {'ready', 'failed', 'indeterminate', 'abstained'} or (
            self.view.receipt.phase == 'proposed' and self.view.proposal is not None
            and self.view.proposal.outcome.kind == 'request_capabilities')
