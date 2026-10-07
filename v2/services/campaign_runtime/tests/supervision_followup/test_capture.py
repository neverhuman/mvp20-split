import pytest
from amphora_campaign_runtime.supervision_responses import SupervisionResponseBinding
from amphora_campaign_runtime.supervision_responses.capture import proposal_from_capture

from .support import exchange


def test_exact_new_capture_replays_with_unresolved_points_and_no_execution_effect():
    original, footprint, response, raw = exchange()
    bound = SupervisionResponseBinding.bind(original, footprint, response,
        actor_id=original.document().planning_request.actor_id, capture_bytes=raw)
    assert bound.document() == response
    parsed = proposal_from_capture(original.document().planning_request, response.observation, raw)
    assert parsed.targets and parsed.unresolved and parsed.scientific_authority == 'not_established'


@pytest.mark.parametrize('case,code', [('duplicate', 'followup_duplicate_criterion'),
    ('blank', 'followup_empty_intent'), ('abstain_targets', 'followup_abstention_targets'),
    ('focus', 'followup_focus_unselected'), ('scope', 'candidate_scope_mismatch')])
def test_internal_consistency_does_not_allow_foreign_scope_or_implicit_focus(case, code):
    def change(value, request):
        if case == 'duplicate': value['targets'] *= 2
        elif case == 'blank': value['targets'][0]['expected_learning'] = ' '
        elif case == 'abstain_targets': value.update(action='abstain', evidence_requests=[])
        elif case == 'focus': value['focus_artifact'] = request.planning_request.context.policy.model_dump(mode='json')
        else: value['targets'][0]['criterion']['question']['scope']['project_id'] = 'foreign'
    original, footprint, response, raw = exchange(change)
    with pytest.raises(ValueError, match=code):
        SupervisionResponseBinding.bind(original, footprint, response,
            actor_id=original.document().planning_request.actor_id, capture_bytes=raw)
