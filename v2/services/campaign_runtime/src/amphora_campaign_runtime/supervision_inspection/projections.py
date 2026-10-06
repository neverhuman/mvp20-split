"""Focused projection objects own metadata selection and winner/proposal distinctions."""

from dataclasses import dataclass

from amphora_contracts_supervision import (
    CheckpointInspectionAttempt,
    CheckpointInspectionItem,
    CheckpointRequestItem,
    CheckpointResponseItem,
    SupervisionRef,
)


@dataclass(frozen=True)
class CheckpointProjection:
    slot: object
    winner: object
    requests: int

    def to_wire(self):
        seed = self.slot.seed.document()
        cut = seed.snapshot.cut
        outcome = None if self.winner is None else self.winner.document().outcome
        return CheckpointInspectionItem(
            reference=SupervisionRef(scope=cut.scope, run_id=cut.run_id, decision_id=self.slot.seed.decision_id),
            checkpoint_id=seed.checkpoint_id,
            targets=tuple(item.activation_id for item in seed.snapshot.checkpoints),
            eligibility_reason=self.slot.reason_code, requests=self.requests,
            winner_kind=None if outcome is None else outcome.kind,
            winner_reason=None if outcome is None else getattr(outcome, 'reason_code', None))


@dataclass(frozen=True)
class RequestProjection:
    original: object
    report: object
    disposition: object
    responses: int

    def to_wire(self):
        request = self.original.frame.request
        context = request.planning_request.context
        report = None if self.report is None else self.report.report.document()
        disposition = None if self.disposition is None else self.disposition.document()
        attempts = () if report is None else tuple(CheckpointInspectionAttempt(ordinal=item.attempt.ordinal,
            status=item.status, observation_sha256=item.observation_sha256) for item in report.attempts)
        return CheckpointRequestItem(request_sha256=self.original.frame.request_sha256,
            lineage=request.lineage, engagement=request.planning_request.reference,
            planning_request_sha256=request.planning_request_sha256, model=context.model, prompt=context.prompt,
            limits=context.limits, context_entries=len(context.entries), context_omissions=len(context.omissions),
            report_stop_reason=None if report is None else report.stop_reason, attempts=attempts,
            responses=self.responses, disposition=None if disposition is None else disposition.kind,
            disposition_reason=None if disposition is None else disposition.reason_code)


@dataclass(frozen=True)
class ResponseProjection:
    stored: object
    winner: object

    def to_wire(self):
        response = self.stored.bound.document()
        observation = response.observation
        outcome = None if self.winner is None else self.winner.document().outcome
        selected = (outcome is not None and outcome.kind == 'model_accepted' and
                    outcome.response_sha256 == self.stored.bound.sha256)
        return CheckpointResponseItem(response_id=response.response_id, response_sha256=self.stored.bound.sha256,
            attempt_ordinal=observation.attempt.ordinal, status=observation.status,
            reason_code=observation.reason_code, output_sha256=observation.output_sha256,
            captured_bytes=observation.captured_bytes, output_complete=observation.output_complete,
            capture=response.capture, selected_by_winner=selected)
