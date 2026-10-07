"""Retained response provenance and original policy produce a bounded candidate outcome."""

from dataclasses import dataclass

from amphora_contracts_planning import checkpoint_draft_schema, checkpoint_followup_draft_schema
from amphora_contracts_supervision import (
    AppliedFields,
    CheckpointModelAccepted,
    EffectiveFieldChange,
    RetainedProposal,
)
from sqlalchemy import text

from ..supervision_checkpoints.values import ValueCheckpointSeed
from ..supervision_effects.proposal import select_fields
from ..supervision_journal.current import verify_current
from ..supervision_outcomes.reports import ReportJournal
from ..supervision_responses.capture import proposal_from_capture
from ..supervision_scope.observations import require


@dataclass(frozen=True)
class ModelWinner:
    outcome: CheckpointModelAccepted
    selection: object | None

    @classmethod
    def bind(cls, conn, params, run, slot, current, frame, response):
        request = frame.request
        original = request.planning_request
        seed = slot.seed
        rule = next(item for item in seed.policy.document().checkpoints
                    if item.checkpoint_id == seed.document().checkpoint_id)
        require(request.schema_version == '2' and request.reference.decision_id == seed.decision_id and
                request.checkpoint_id == rule.checkpoint_id and request.reference.scope == seed.footprint().cut.scope and
                request.reference.run_id == seed.footprint().cut.run_id, 'winner_request_slot')
        require(request.policy.sha256 == seed.policy.sha256, 'winner_request_policy')
        latest = conn.execute(text('SELECT max(ordinal) FROM runtime.supervision_requests WHERE '
            'tenant_id=:tenant AND project_id=:project AND run_id=:run AND decision_id=:decision'), params).scalar_one()
        require(request.lineage.ordinal == latest, 'winner_request_superseded')
        report_params = {**params, 'request': frame.request_sha256}
        stored_report = ReportJournal.load(conn, report_params, ReportJournal.source(conn, report_params))
        if stored_report is not None:
            stored_report.report.require_response(response.bound.document())
        require(request.lineage.ordinal <= rule.max_requests and original.context.limits.max_attempts <= rule.max_model_calls,
                'winner_request_ceiling')
        require(request.deadline_unix_ms <= int(slot.deadline.timestamp() * 1000), 'winner_request_deadline')
        require(original.context.output_schema in (checkpoint_draft_schema(), checkpoint_followup_draft_schema()), 'winner_checkpoint_output_required')
        verify_current(conn, params, run, frame)
        require(isinstance(seed, ValueCheckpointSeed), 'winner_requires_scalar_seed')
        candidate_seed = ValueCheckpointSeed.capture(seed.policy, frame.footprint(), seed.document().original_fields)
        require(candidate_seed.decision_id == seed.decision_id, 'winner_request_occurrence')
        record = response.bound.document()
        require(record.request_sha256 == frame.request_sha256 and record.reference == request.reference,
                'winner_response_request')
        draft = proposal_from_capture(original, record.observation, response.capture_bytes)
        if draft.candidate is not None and draft.candidate.kind == 'materialization_adjustment':
            selection = select_fields(candidate_seed, draft)
            selection.resolve(current.document().original_fields)
            selected = selection.document()
            effect = AppliedFields(kind='adjusted_materialization_fields', target=selected.target,
                selection_sha256=selection.sha256, changes=tuple(EffectiveFieldChange(field_name=item.name,
                    previous_value_sha256=item.previous_value_sha256, value=item.value) for item in selected.changes))
        else:
            selection = None
            kind = ('abstained' if draft.action == 'abstain' else
                    'evidence_request' if draft.action == 'request_evidence' else 'future_campaign')
            effect = RetainedProposal(kind=kind, proposal=record.capture, content_sha256=record.capture.sha256)
        outcome = CheckpointModelAccepted(kind='model_accepted', request_sha256=frame.request_sha256,
                                         response_sha256=response.bound.sha256, effect=effect)
        return cls(outcome, selection)
