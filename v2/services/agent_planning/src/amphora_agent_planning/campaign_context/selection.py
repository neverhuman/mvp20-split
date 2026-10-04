"""Immutable selected identities; owner contact and record meaning are separate."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_planning import CampaignResearchSelection
from pydantic import ValidationError

from ..context import RequestSnapshot
from ..context.policy import require
from ..context.snapshot import _constant, _object

MAX_SELECTION_BYTES = 262144


class SelectionPolicy:
    @staticmethod
    def validate(selection, request):
        original = request.document()
        require(original.purpose in {"campaign_proposal", "supervision"}, "campaign_context_purpose")
        require(selection.engagement == original.reference, "campaign_context_engagement")
        require(selection.request_sha256 == request.sha256, "campaign_context_request")
        scope = original.reference.scope
        for refs, field in ((selection.questions, "question_id"), (selection.needs, "need_id")):
            seen = set()
            for ref in refs:
                require(ref.scope == scope, "campaign_context_scope")
                identity = (getattr(ref, field), ref.revision)
                require(identity not in seen, "campaign_context_duplicate_reference")
                seen.add(identity)
        selected = {entry.artifact.artifact_id: entry.artifact for entry in original.context.entries}
        assessments = set()
        for item in selection.assessments:
            assessment = item.request
            require(assessment.profile.scope == scope and assessment.question.scope == scope,
                    "campaign_context_scope")
            require(assessment.assessment_id not in assessments, "campaign_context_duplicate_assessment")
            assessments.add(assessment.assessment_id)
            require(assessment.question in selection.questions, "campaign_context_question_unselected")
            criteria = [answer.criterion_id for answer in assessment.answers]
            require(len(set(criteria)) == len(criteria), "campaign_context_duplicate_criterion")
            receipts = [ref.artifact_id for ref in assessment.receipts]
            require(len(set(receipts)) == len(receipts), "campaign_context_duplicate_receipt")
            for ref in (*assessment.receipts, *(answer.artifact for answer in assessment.answers)):
                require(ref.scope == scope, "campaign_context_scope")
                require(selected.get(ref.artifact_id) == ref, "campaign_context_artifact_unselected")


@dataclass(frozen=True)
class ResearchSelection:
    canonical: bytes
    request: RequestSnapshot

    @classmethod
    def from_bytes(cls, raw, request):
        require(type(raw) is bytes and 0 < len(raw) <= MAX_SELECTION_BYTES, "campaign_context_size")
        original = request.document()
        request = RequestSnapshot.bind(original, actor_id=original.actor_id, scope=original.reference.scope)
        try:
            value = json.loads(raw.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
            selection = CampaignResearchSelection.model_validate_json(json.dumps(value, allow_nan=False))
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError, RecursionError) as error:
            raise ValueError("invalid_campaign_context_selection") from error
        SelectionPolicy.validate(selection, request)
        canonical = json.dumps(selection.model_dump(mode="json"), sort_keys=True, separators=(",", ":"),
                               ensure_ascii=False, allow_nan=False).encode("utf-8")
        require(len(canonical) <= MAX_SELECTION_BYTES, "campaign_context_size")
        return cls(canonical, request)

    @classmethod
    def bind(cls, selection, request):
        return cls.from_bytes(selection.model_dump_json(warnings=False).encode("utf-8"), request)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def document(self):
        return CampaignResearchSelection.model_validate_json(self.canonical)
