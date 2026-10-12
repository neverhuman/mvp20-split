"""Owner-reviewed limits remain independent of human intent and model output."""
from dataclasses import dataclass
import hashlib
import json

from amphora_contracts_core import ArtifactRef
from ..budget import BudgetPolicy
from ..campaign_context.records import canonical
from ..campaign_decisions import DecisionDeclaration
from ..context import RequestSnapshot
from ..context.policy import require
from ..context.snapshot import _object, _constant
from ..curation_budget import CurationAllowance
from ..curation_context import CurationIntent
from ..curation_runtime import CurationRuntimeContext
from .wire import PolicyRecord


@dataclass(frozen=True)
class ReviewedDeclaration:
    intent: CurationIntent
    declaration: DecisionDeclaration
    budget: BudgetPolicy

    def with_artifact(self, reference):
        reference = ArtifactRef.model_validate_json(reference.model_dump_json())
        request = self.intent.request.document()
        require(reference.scope == request.reference.scope and reference.sha256 == self.declaration.sha256
                and reference.size_bytes == len(self.declaration.canonical) and reference.media_type == 'text/plain',
                'curation_declaration_artifact')
        value = request.model_dump(mode='json')
        value['decision_scope'] = self.declaration.sha256
        value['context']['entries'].append({'artifact': reference.model_dump(mode='json'),
                                           'role': 'constraint', 'required': True})
        bound = RequestSnapshot.from_bytes(canonical(value), actor_id=request.actor_id, scope=request.reference.scope)
        from ..curation_intake.commands import CurationCommand
        incoming = CurationCommand.restore(canonical(json.loads(self.intent.canonical)['command']))
        return CurationIntent.bind(bound, incoming)


@dataclass(frozen=True)
class CurationPolicy:
    canonical: bytes

    @classmethod
    def from_bytes(cls, raw):
        require(type(raw) is bytes and 0 < len(raw) <= 262144, 'curation_policy_size')
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
        record = PolicyRecord.model_validate_json(canonical(value))
        template = record.template
        RequestSnapshot.bind(template, actor_id=template.actor_id, scope=template.reference.scope)
        require(template.purpose == 'campaign_proposal' and template.runtime_cut is None
                and not template.context.entries and not template.context.omissions, 'curation_policy_template')
        require(set(template.context.allowed_actions) == {'abstain', 'propose_campaign'}, 'curation_policy_actions')
        require(len(set(record.future.side_effects)) == len(record.future.side_effects), 'curation_policy_effects')
        result = cls(canonical(record.model_dump(mode='json')))
        CurationAllowance.validate_policy(result.budget())
        return result

    def document(self):
        return PolicyRecord.model_validate_json(self.canonical)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def budget(self):
        record = self.document()
        context = record.template.context.model_dump(mode='json')
        value = {key: context[key] for key in ('model', 'prompt', 'policy', 'output_schema', 'allowed_actions', 'limits')}
        value.update(format='planning-budget-policy.v1', per_attempt_accounting_units=record.reservation_units)
        budget = BudgetPolicy.from_bytes(canonical(value))
        CurationAllowance.validate_policy(budget)
        return budget

    def seed(self, incoming):
        require(self.from_bytes(self.canonical).canonical == self.canonical, 'curation_policy_canonical')
        record = self.document()
        template = RequestSnapshot.bind(record.template, actor_id=record.template.actor_id, scope=record.template.reference.scope)
        return CurationIntent.from_template(template, incoming, record.policy_id)

    def declare(self, supplied):
        original = CurationRuntimeContext.from_payload(supplied.intent, json.loads(supplied.canonical))
        from ..curation_intake.commands import CurationCommand
        incoming = CurationCommand.restore(canonical(json.loads(original.intent.canonical)['command']))
        seed = self.seed(incoming)
        require(seed == original.intent, 'curation_policy_original_request')
        record = self.document()
        template = seed.request.document()
        selected = incoming.request.payload.context
        draft = json.loads(original.canonical)['draft']['definition']
        pins = {}
        def pin(kind, identity, revision, digest):
            value = {'kind': kind, 'identity': identity, 'revision': revision, 'sha256': digest}
            old = pins.setdefault((kind, identity), value)
            require(old == value, 'curation_policy_context_conflict')
        for kind, reference in [('source', template.context.objective), ('policy', template.context.policy),
                                ('model', template.context.model.configuration)]:
            pin(kind, reference.artifact_id, '1', reference.sha256)
        for reference in selected.artifacts:
            pin('source', reference.artifact_id, '1', reference.sha256)
        for head in selected.knowledge:
            pin('knowledge', head.snapshot.graph.graph_id, str(head.snapshot.revision), head.snapshot.sha256)
        future = record.future.model_dump(mode='json')
        future.update(campaign_id=draft['campaign_id'], revision=draft['revision'] + 1, context=list(pins.values()))
        declaration = DecisionDeclaration.from_bytes(canonical({
            'format': 'planning-campaign-decision.v2', 'engagement': template.reference.model_dump(mode='json'),
            'objective': template.context.objective.model_dump(mode='json'),
            'policy': template.context.policy.model_dump(mode='json'), 'runtime_cut': None,
            'allowed_actions': ['abstain', 'propose_campaign'], 'eligibility_context': record.eligibility_context,
            'future': future, 'adjustments': []}))
        return ReviewedDeclaration(seed, declaration, self.budget())
