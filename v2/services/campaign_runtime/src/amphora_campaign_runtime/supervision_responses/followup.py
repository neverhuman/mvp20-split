"""Future intent consistency, not Research membership or scientific acceptance."""

from ..supervision_requests.binding import encoded
from ..supervision_scope.observations import require


def validate_followup(original, draft):
    require(draft.action != 'abstain' or not draft.targets, 'followup_abstention_targets')
    if draft.focus_artifact is not None:
        require(any(entry.artifact == draft.focus_artifact for entry in original.context.entries),
                'followup_focus_unselected')
    references = {}
    for items in (draft.targets, draft.unresolved):
        seen = set()
        for item in items:
            ref = item.criterion
            key = (encoded(ref.question), encoded(ref.need), ref.criterion_id)
            require(key not in seen, 'followup_duplicate_criterion')
            seen.add(key)
            require(references.setdefault(key, ref) == ref, 'followup_criterion_conflict')
            require(ref.assessment is None or ref.assessment.request.question == ref.question,
                    'followup_assessment_question')
    for target in draft.targets:
        require(target.improvement.strip() and target.expected_learning.strip(), 'followup_empty_intent')
