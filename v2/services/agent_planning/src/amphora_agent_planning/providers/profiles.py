"""Closed schema catalog; model text never selects executable handlers."""

import hashlib
import json

from amphora_contracts_planning import (
    ExtractionDraft,
    ExtractionDraftV2,
    ProviderObservation,
    TaskProviderObservation,
    TypedProposal,
    campaign_draft_schema,
    checkpoint_draft_schema,
    checkpoint_followup_draft_schema,
    extraction_draft_schema,
    extraction_edit_schema,
    reference_proposal_schema,
)
from pydantic import ValidationError

from ..campaign_output import CampaignOutput
from ..campaign_output.checkpoint import CheckpointOutput
from ..campaign_followup.output import FollowupOutput
from ..context.policy import require
from ..context.snapshot import _constant, _object
from .proposal import ProposalPolicy


class OutputProfiles:
    @staticmethod
    def draft_model(profile):
        if profile == extraction_draft_schema():
            return ExtractionDraft
        require(profile == extraction_edit_schema(), "unsupported_output_profile")
        return ExtractionDraftV2

    @staticmethod
    def attributed_items(draft):
        groups = ("entities", "assertions", "questions", "answers", "evidence_needs")
        if isinstance(draft, ExtractionDraftV2):
            groups += ("edits",)
        for group in groups:
            for index, item in enumerate(getattr(draft, group)):
                yield f"/{group}/{index}", item

    @staticmethod
    def supported(attempt):
        return attempt.request.document().context.output_schema in (reference_proposal_schema(),
            extraction_draft_schema(), extraction_edit_schema(), campaign_draft_schema(), checkpoint_draft_schema(),
            checkpoint_followup_draft_schema())

    @staticmethod
    def observation_model(attempt):
        if attempt.request.document().context.output_schema in (extraction_draft_schema(), extraction_edit_schema(),
                campaign_draft_schema(), checkpoint_draft_schema(), checkpoint_followup_draft_schema()):
            return TaskProviderObservation
        return ProviderObservation

    @classmethod
    def parse(cls, raw, attempt):
        profile = attempt.request.document().context.output_schema
        if profile == reference_proposal_schema():
            return ProposalPolicy.parse(raw, attempt)
        if profile == campaign_draft_schema():
            return CampaignOutput.parse(raw, attempt.request).proposal()
        if profile == checkpoint_draft_schema():
            return CheckpointOutput.parse(raw, attempt.request).proposal()
        if profile == checkpoint_followup_draft_schema():
            return FollowupOutput.parse(raw, attempt.request).proposal()
        model = cls.draft_model(profile)
        require(type(raw) is bytes and 0 < len(raw) <= 65536, "typed_output_size")
        try:
            value = json.loads(raw.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
            draft = model.model_validate_json(json.dumps(value, allow_nan=False))
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError, RecursionError) as exc:
            raise ValueError("invalid_output") from exc
        context = attempt.request.document().context
        require(draft.action in context.allowed_actions, "action_not_allowed")
        require(draft.action != "abstain" or not any(cls.attributed_items(draft)), "abstention_payload")
        cls._references(draft, context)
        canonical = json.dumps(draft.model_dump(mode="json"), sort_keys=True, separators=(",", ":"),
                               ensure_ascii=False, allow_nan=False).encode("utf-8")
        require(len(canonical) <= 65536, "typed_output_size")
        return TypedProposal(output_schema=profile, action=draft.action, rationale=draft.rationale,
                             payload_json=canonical.decode("utf-8"), payload_sha256=hashlib.sha256(canonical).hexdigest())

    @staticmethod
    def _references(draft, context):
        selected = [entry.artifact for entry in context.entries]
        sources = [entry.artifact for entry in context.entries if entry.role == "source"]
        for _, item in OutputProfiles.attributed_items(draft):
            for quote in item.attribution.quotations:
                require(quote.span.source.scope == context.scope, "proposal_scope_mismatch")
                require(quote.span.source.raw in sources, "unselected_payload")
        for entity in draft.entities:
            require(all(match.graph.scope == context.scope for match in entity.matches), "proposal_scope_mismatch")
        for item in (*draft.answers, *draft.evidence_needs):
            require(item.question is None or item.question.scope == context.scope, "proposal_scope_mismatch")
        artifacts = [item.applicability for item in (*draft.assertions, *draft.questions)]
        artifacts += [item.context for item in draft.answers]
        artifacts += [item.required_context for item in draft.evidence_needs]
        if isinstance(draft, ExtractionDraftV2):
            artifacts += [item.context for item in draft.entities]
            for edit in draft.edits:
                for name in ("prior", "assertion", "source", "target"):
                    reference = getattr(edit, name, None)
                    require(reference is None or reference.graph.scope == context.scope, "proposal_scope_mismatch")
        require(all(artifact is None or artifact in selected for artifact in artifacts), "unselected_payload")
