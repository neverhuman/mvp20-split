"""Explicit public checkpoint proposal to pure policy selection, not SQL acceptance."""

from amphora_contracts_planning import CheckpointDraft, MaterializationAdjustmentDraft

from ..supervision_scope.observations import require
from .selection import FieldChange, ScalarSelection


def select_fields(seed, draft):
    record = CheckpointDraft.model_validate_json(draft.model_dump_json())
    candidate = record.candidate
    require(record.action == 'propose_campaign' and isinstance(candidate, MaterializationAdjustmentDraft),
            'selection_materialization_proposal_required')
    require(candidate.checkpoint_seed_sha256 == seed.sha256 and candidate.cut == seed.footprint().cut,
            'selection_proposal_seed')
    target = candidate.changes[0].target
    require(all(change.target == target for change in candidate.changes), 'selection_multiple_occurrences')
    changes = tuple(FieldChange(name=item.field_name, previous_value_sha256=item.previous_value_sha256,
                                value=item.proposed) for item in candidate.changes)
    return ScalarSelection.bind(seed, target, changes)
