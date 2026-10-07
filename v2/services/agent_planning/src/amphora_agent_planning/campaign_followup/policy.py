"""Bind future intent to explicit selected identities and retained Research records."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_planning import (
    CampaignFollowupSelection,
    CheckpointFollowupDraft,
    checkpoint_followup_draft_schema,
)

from ..context.policy import require


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')


def criterion_key(reference):
    return canonical(reference.model_dump(mode='json', exclude={'assessment'}))


class FollowupSelectionPolicy:
    @staticmethod
    def validate(selection, request):
        original = request.document()
        require(original.context.output_schema == checkpoint_followup_draft_schema(), 'followup_profile')
        seen = set()
        for ref in selection.criteria:
            require(ref.question in selection.questions and ref.need in selection.needs, 'followup_reference_unselected')
            require(ref.question.scope == original.reference.scope and ref.need.scope == original.reference.scope,
                    'followup_scope')
            key = criterion_key(ref)
            require(key not in seen, 'followup_duplicate_criterion')
            seen.add(key)
            if ref.assessment is not None:
                require(ref.assessment in selection.assessments and ref.assessment.request.question == ref.question,
                        'followup_assessment_unselected')
        if selection.focus_artifact is not None:
            require(any(entry.artifact == selection.focus_artifact for entry in original.context.entries),
                    'followup_focus_unselected')
            require(selection.focus_artifact.scope == original.reference.scope, 'followup_scope')


@dataclass(frozen=True)
class CriterionBindings:
    """Factory-validated membership; retained canonical bytes cannot drift with caller DTOs."""

    selection_bytes: bytes

    @classmethod
    def bind(cls, supplied, *, questions, needs, assessments):
        selection = CampaignFollowupSelection.model_validate_json(supplied.model_dump_json(warnings=False))
        question_map = {record.reference: record for record in questions}
        need_map = {record.reference: record for record in needs}
        assessment_map = {record.request.assessment_id: record for record in assessments}
        require(len(question_map) == len(questions) and len(need_map) == len(needs) and
                len(assessment_map) == len(assessments), 'followup_duplicate_record')
        seen = set()
        for ref in selection.criteria:
            key = criterion_key(ref)
            require(key not in seen, 'followup_duplicate_criterion')
            seen.add(key)
            require(ref.question in selection.questions and ref.need in selection.needs, 'followup_reference_unselected')
            question, need = question_map.get(ref.question), need_map.get(ref.need)
            require(question is not None and need is not None, 'followup_criterion_record_unavailable')
            require(need.question == ref.question, 'followup_need_question')
            require(ref.criterion_id in need.criterion_ids and
                    any(item.criterion_id == ref.criterion_id for item in question.criteria), 'followup_criterion_missing')
            if ref.assessment is not None:
                require(ref.assessment in selection.assessments and ref.assessment.request.question == ref.question,
                        'followup_assessment_unselected')
                status = assessment_map.get(ref.assessment.request.assessment_id)
                require(status is not None and status.request == ref.assessment.request, 'followup_assessment_record_unavailable')
                require(hashlib.sha256(canonical(status.model_dump(mode='json'))).hexdigest() == ref.assessment.status_sha256,
                        'followup_assessment_digest')
                require(status.outcome.status == 'assessed' and any(
                    item.need == ref.need and item.criterion_id == ref.criterion_id
                    for item in status.outcome.assessment.needs), 'followup_assessment_criterion')
        return cls(canonical(selection.model_dump(mode='json')))

    def document(self):
        return CampaignFollowupSelection.model_validate_json(self.selection_bytes)

    def validate_output(self, supplied):
        draft = CheckpointFollowupDraft.model_validate_json(supplied.model_dump_json(warnings=False))
        selected = self.document()
        require(draft.focus_artifact == selected.focus_artifact, 'followup_focus_mismatch')
        expected = {criterion_key(ref): ref for ref in selected.criteria}
        covered = set()
        for items in (draft.targets, draft.unresolved):
            seen = set()
            for item in items:
                key = criterion_key(item.criterion)
                require(expected.get(key) == item.criterion, 'followup_output_unselected')
                require(key not in seen, 'followup_output_duplicate')
                seen.add(key)
                covered.add(key)
        require(covered == set(expected), 'followup_output_omitted')
        require(draft.action != 'abstain' or not draft.targets, 'followup_abstention_targets')
        for target in draft.targets:
            require(target.improvement.strip() and target.expected_learning.strip(), 'followup_empty_intent')
        return draft
