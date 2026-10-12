"""Reconstruct original identities; never infer provenance from similar graphs."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_planning import (
    CampaignOriginV2 as CampaignOrigin, CampaignOriginBodyV2 as CampaignOriginBody, CampaignOriginDraft, CampaignOriginProposal,
    CampaignOriginResearch, CampaignOriginResearchRecord, CampaignOriginSave, CampaignOriginTool,
)

from ..campaign_context.records import canonical
from ..campaign_dispatch.effect import CompilerEffect
from ..campaign_dispatch.observation import CompilerObservation
from ..campaign_proposals.research import ConsumedResearch
from ..context.policy import require
from .knowledge import KnowledgeOrigin

MAX_RESPONSE_BYTES = 262144


def digest(value):
    return hashlib.sha256(canonical(value.model_dump(mode='json'))).hexdigest()


@dataclass(frozen=True)
class OriginProjection:
    canonical: bytes

    @classmethod
    def bind(cls, principal, selection, authoring, eligibility, observation):
        """Called only after the owned journal reconstructs original history.

        This is pure verification, not proof of durable storage by itself. HTTP
        callers cannot supply these objects or the original producer principal.
        """
        selection.verify_origin(principal, authoring, eligibility)
        effect = CompilerEffect.authoring(selection, principal, authoring, eligibility)
        request = authoring.save()
        observation = CompilerObservation.restore(observation.canonical, selection, effect, request)
        require(observation.status == 'saved', 'origin_saved_required')
        outcome = observation.outcome
        prepared = authoring.review.composition.evidence.proposal
        original = prepared.attempt.request.document()
        output = prepared.review_document()
        readback = outcome.readback
        draft = CampaignOriginDraft(scope=readback.scope, draft_id=readback.head.draft_id,
            revision=readback.head.revision, content_sha256=readback.head.content_sha256)
        proposal = CampaignOriginProposal(actor_id=original.actor_id, attempt=prepared.attempt.reference(),
            preparation_sha256=prepared.inputs.preparation.sha256, prepared_proposal_sha256=prepared.sha256,
            output_sha256=prepared.output.sha256, action=output.action, rationale=output.rationale,
            context=original.context, usage=prepared.observation.document().usage,
            capture_publication='not_published')
        save = CampaignOriginSave(owner_id=request.owner_id, selection_id=selection.effect_id,
            selection_sha256=selection.sha256, effect_id=effect.effect_id, effect_sha256=effect.sha256,
            receipt=outcome.receipt, readback_sha256=digest(readback))
        body = CampaignOriginBody(authority='historical_compiler_provenance', draft=draft,
            proposal=proposal, save=save, research=cls.research(prepared), knowledge=KnowledgeOrigin.from_proposal(prepared),
            tools=tuple(CampaignOriginTool(node=use.address, release=use.release.record.document().lock)
                        for use in authoring.review.composition.uses),
            limitations=('historical_only', 'scientific_authority_not_established',
                         'current_eligibility_not_checked', 'capture_not_published'))
        value = CampaignOrigin(origin_sha256=digest(body), origin=body)
        return cls.restore(canonical(value.model_dump(mode='json')), draft)

    @staticmethod
    def research(prepared):
        consumed = ConsumedResearch.from_proposal(prepared)
        if consumed is None:
            return CampaignOriginResearch(selection=None, records=())
        context = consumed.context
        records = []
        for record in context.records:
            document = record.document()
            criteria = (tuple(item.criterion_id for item in document.criteria) if record.identity.kind == 'question'
                        else document.criterion_ids if record.identity.kind == 'need' else ())
            records.append(CampaignOriginResearchRecord(kind=record.identity.kind,
                reference=document.request if record.identity.kind == 'assessment' else document.reference,
                record_sha256=record.sha256, unavailable=None, criterion_ids=criteria))
        from ..campaign_context.records import REFERENCE_MODELS
        for gap in context.gaps:
            records.append(CampaignOriginResearchRecord(kind=gap.identity.kind,
                reference=REFERENCE_MODELS[gap.identity.kind].model_validate_json(gap.identity.reference),
                record_sha256=None, unavailable=gap.reason, criterion_ids=()))
        return CampaignOriginResearch(selection=context.selection.document(), records=tuple(records))

    @classmethod
    def restore(cls, raw, expected):
        require(type(raw) is bytes and 0 < len(raw) <= MAX_RESPONSE_BYTES, 'origin_response_limit')
        value = CampaignOrigin.model_validate_json(raw)
        body = value.origin
        require(canonical(value.model_dump(mode='json')) == raw, 'origin_canonical')
        require(body.draft == expected, 'origin_draft_mismatch')
        require(value.origin_sha256 == digest(body), 'origin_digest_mismatch')
        scope = expected.scope
        require(body.proposal.attempt.engagement.scope == scope == body.proposal.context.scope,
                'origin_scope_mismatch')
        knowledge = body.knowledge
        if knowledge is not None:
            require(knowledge.graph.scope == scope, 'origin_knowledge_scope')
            if knowledge.status == 'available':
                from ..graph_context import GraphPins
                require(knowledge.vocabulary is not None and knowledge.policy is not None and
                        knowledge.context_sha256 is not None and knowledge.unavailable is None,
                        'origin_knowledge_available')
                GraphPins(knowledge.graph, knowledge.head, knowledge.vocabulary, knowledge.policy).validated()
                require(all(ref.graph == knowledge.graph for ref in (*knowledge.entities, *knowledge.assertions)) and
                        len(set(knowledge.entities)) == len(knowledge.entities) and
                        len(set(knowledge.assertions)) == len(knowledge.assertions) and
                        (knowledge.head is not None or not (knowledge.entities or knowledge.assertions)),
                        'origin_knowledge_selection')
            else:
                require(knowledge.head is None and knowledge.vocabulary is None and knowledge.policy is None and
                        not knowledge.entities and not knowledge.assertions and knowledge.context_sha256 is None and
                        knowledge.unavailable is not None, 'origin_knowledge_unavailable')
        outcome = body.save.receipt.outcome
        require(outcome.status == 'accepted', 'origin_saved_required')
        require(outcome.binding.identity.scope == scope and
                outcome.binding.identity.command_family == 'definition.save', 'origin_save_binding')
        commit = outcome.committed
        require(commit.kind == 'draft_revision' and commit.object_id == expected.draft_id and
                commit.revision == expected.revision and commit.content_sha256 == expected.content_sha256,
                'origin_save_binding')
        selection = body.research.selection
        if selection is None:
            require(not body.research.records, 'origin_research_selection')
        else:
            require(selection.engagement == body.proposal.attempt.engagement and
                    selection.request_sha256 == body.proposal.attempt.request_sha256,
                    'origin_research_selection')
            expected_records = {('question', canonical(ref.model_dump(mode='json'))) for ref in selection.questions}
            expected_records.update(('need', canonical(ref.model_dump(mode='json'))) for ref in selection.needs)
            expected_records.update(('assessment', canonical(item.request.model_dump(mode='json')))
                                    for item in selection.assessments)
            actual_records = set()
            for record in body.research.records:
                key = (record.kind, canonical(record.reference.model_dump(mode='json')))
                require(key in expected_records and key not in actual_records, 'origin_research_records')
                require((record.record_sha256 is None) == (record.unavailable is not None), 'origin_research_gap')
                require(not record.criterion_ids or (record.unavailable is None and record.kind != 'assessment'),
                        'origin_research_criteria')
                require(len(set(record.criterion_ids)) == len(record.criterion_ids), 'origin_research_criteria')
                actual_records.add(key)
            require(actual_records == expected_records, 'origin_research_records')
        return cls(raw)

    def document(self):
        return CampaignOrigin.model_validate_json(self.canonical)
