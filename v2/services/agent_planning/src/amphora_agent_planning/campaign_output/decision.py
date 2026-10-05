"""Original request identity bounds interpretation, never adjustment permission."""

from dataclasses import dataclass

from amphora_contracts_core import Scope, WireModel
from amphora_contracts_planning import campaign_draft_schema

from ..context import RequestSnapshot
from ..context.policy import require


@dataclass(frozen=True)
class CampaignDecisionScope:
    request: RequestSnapshot

    @classmethod
    def bind(cls, request):
        original = request.document()
        checked = RequestSnapshot.bind(original, actor_id=original.actor_id, scope=original.reference.scope)
        require(original.purpose in {'campaign_proposal', 'supervision'}, 'campaign_output_purpose')
        require(original.context.output_schema == campaign_draft_schema(), 'campaign_output_profile')
        return cls(checked)

    def validate(self, draft):
        original = self.request.document()
        require(draft.decision_scope == original.decision_scope, 'campaign_decision_scope')
        require(draft.action in original.context.allowed_actions, 'action_not_allowed')
        self._references(draft, original.reference.scope)

    @staticmethod
    def _references(value, expected):
        # Traverse typed public values, not model-selected field names. This
        # includes nested Artifact, assessment, graph and Runtime references.
        pending = [value]
        while pending:
            item = pending.pop()
            if isinstance(item, Scope):
                require(item == expected, 'campaign_output_scope')
            elif isinstance(item, WireModel):
                pending.extend(getattr(item, field) for field in type(item).model_fields)
            elif isinstance(item, tuple):
                pending.extend(item)
