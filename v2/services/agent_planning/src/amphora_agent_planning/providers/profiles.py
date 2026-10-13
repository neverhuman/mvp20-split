"""Closed schema catalog; model text never selects executable handlers."""

import hashlib
import json
from functools import lru_cache

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
from amphora_contracts_campaign_curation import campaign_curation_draft_schema
from pydantic import ValidationError

from ..campaign_output import CampaignOutput
from ..curation_output import CurationOutput
from ..campaign_output.checkpoint import CheckpointOutput
from ..campaign_followup.output import FollowupOutput
from ..context.policy import require
from ..context.snapshot import _constant, _object
from .proposal import ProposalPolicy


def _identity(profile):
    return (profile.schema_id, profile.version, profile.sha256)


@lru_cache(maxsize=1)
def _profile_catalog():
    # Installed contract schemas are static. Retain scalar identities only;
    # request data, observations, permissions and handler objects are not cached.
    return tuple((name, _identity(factory())) for name, factory in (
        ('reference', reference_proposal_schema), ('extraction', extraction_draft_schema),
        ('extraction_edit', extraction_edit_schema), ('campaign', campaign_draft_schema),
        ('checkpoint', checkpoint_draft_schema), ('followup', checkpoint_followup_draft_schema),
        ('curation', campaign_curation_draft_schema)))


def _profile_kind(profile):
    identity = _identity(profile)
    return next((name for name, expected in _profile_catalog() if identity == expected), None)


class OutputProfiles:
    @staticmethod
    def draft_model(profile):
        kind = _profile_kind(profile)
        if kind == 'extraction':
            return ExtractionDraft
        require(kind == 'extraction_edit', "unsupported_output_profile")
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
        return _profile_kind(attempt.request.document().context.output_schema) is not None

    @staticmethod
    def observation_model(attempt):
        if _profile_kind(attempt.request.document().context.output_schema) in (
                'extraction', 'extraction_edit', 'campaign', 'checkpoint', 'followup', 'curation'):
            return TaskProviderObservation
        return ProviderObservation

    @classmethod
    def parse(cls, raw, attempt):
        profile = attempt.request.document().context.output_schema
        kind = _profile_kind(profile)
        if kind == 'reference':
            return ProposalPolicy.parse(raw, attempt)
        if kind == 'curation':
            return CurationOutput.parse(raw, attempt.request).proposal()
        if kind == 'campaign':
            return CampaignOutput.parse(raw, attempt.request).proposal()
        if kind == 'checkpoint':
            return CheckpointOutput.parse(raw, attempt.request).proposal()
        if kind == 'followup':
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
