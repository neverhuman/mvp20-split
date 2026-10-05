"""Combined bounded proposal review; reservation, admission and application are separate."""

from dataclasses import dataclass

from amphora_contracts_planning import CampaignAdjustmentDraft

from ..budget import BudgetPolicy
from ..budget.policy import ReservationDemand
from ..campaign_context.records import canonical
from ..campaign_proposals import CompositionReview
from ..campaign_proposals.observations import ObservationKey, RelevantReadSet
from ..context.policy import require
from .adjustments import AdjustmentPermissions
from .declaration import DecisionDeclaration
from .wire import FutureBoundaryRecord


@dataclass(frozen=True)
class FutureDecisionBoundary:
    limits: FutureBoundaryRecord | None

    def validate(self, composition):
        require(self.limits is not None, 'decision_future_not_permitted')
        authored = composition.authored
        definition = authored.candidate.definition
        limits = self.limits
        require(definition.campaign_id == limits.campaign_id and definition.revision == limits.revision,
                'decision_future_identity')
        require(len(set(definition.context)) == len(definition.context) and set(definition.context) == set(limits.context),
                'decision_future_context')
        require(len(authored.nodes) <= limits.max_nodes, 'decision_future_nodes')
        require(len({row.address.scope_path for row in authored.nodes}) <= limits.max_scopes, 'decision_future_scopes')
        require(max(len(row.address.scope_path) for row in authored.nodes) <= limits.max_depth, 'decision_future_depth')
        for row in authored.nodes:
            if row.node.kind == 'iterate':
                require(row.node.max_iterations <= limits.max_iterations, 'decision_future_iterations')
            elif row.node.kind == 'invoke':
                require(row.node.timeout_seconds <= limits.max_tool_timeout, 'decision_future_timeout')
        require(all(use.release.record.document().descriptor.tool.side_effects in limits.side_effects for use in composition.uses),
                'decision_future_side_effect')


@dataclass(frozen=True)
class CampaignDecisionReview:
    composition: CompositionReview
    declaration: DecisionDeclaration
    demand: ReservationDemand
    read_set: RelevantReadSet
    next_step: str

    @classmethod
    def bind(cls, prepared, declaration, reviewed_budget):
        composition = CompositionReview.bind(prepared)
        prepared = composition.evidence.proposal
        key = declaration.bind(prepared)
        policy = declaration.document()
        draft = prepared.output.document()
        require(draft.action in policy.allowed_actions, 'decision_action_not_permitted')
        budget = BudgetPolicy.from_bytes(reviewed_budget.canonical)
        require(budget == reviewed_budget, 'decision_budget_binding')
        demand = budget.demand(prepared.attempt)
        require(all(policy.eligibility_context in use.release.record.document().descriptor.tool.applicability for use in composition.uses),
                'decision_tool_applicability')
        if composition.authored is not None:
            FutureDecisionBoundary(policy.future).validate(composition)
            next_step = 'compile_future_draft'
        elif isinstance(draft.candidate, CampaignAdjustmentDraft):
            AdjustmentPermissions.bind(policy.adjustments).validate(draft.candidate)
            next_step = 'runtime_adjustment_unavailable'
        else:
            next_step = 'abstained' if draft.action == 'abstain' else 'evidence_request'
        keys = set(composition.read_set.keys) | {key}
        keys.update(ObservationKey('artifact', 'artifact', canonical(reference.model_dump(mode='json')))
                    for reference in (policy.objective, policy.policy))
        return cls(composition, declaration, demand, prepared.inputs.select(keys), next_step)
