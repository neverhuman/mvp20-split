"""One deterministic prepared engagement from exact facts and immutable predecessors."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef, Identifier
from amphora_contracts_planning import (
    ContextEntry,
    ContextManifest,
    EngagementRef,
    EngagementRequest,
    checkpoint_draft_schema,
)
from amphora_contracts_supervision import (
    CheckpointContext,
    CheckpointFieldContext,
    CheckpointRequest,
    SupervisionLineage,
    checkpoint_context_schema,
)
from pydantic import TypeAdapter

from ..compiler.catalog import canonical
from ..supervision_effects.selection import scalar_digest
from ..supervision_journal.checkpoint_frames import CheckpointFrame, read_frame
from ..supervision_journal.series import RequestSeries
from ..supervision_requests.binding import encoded
from ..supervision_scope.observations import require
from .basis import ContextBasis


@dataclass(frozen=True)
class ContextSession:
    basis: ContextBasis
    previous: tuple
    planning_actor: str

    def __post_init__(self):
        TypeAdapter(Identifier).validate_python(self.planning_actor)
        require(type(self.previous) is tuple, 'context_previous_history')
        previous = tuple(read_frame(item.canonical) for item in self.previous)
        if previous:
            RequestSeries(previous)
        for item in previous:
            require(item.request.reference == self.basis.reference and
                    item.request.planning_request.actor_id == self.planning_actor, 'context_previous_binding')
        charges = tuple(item for item in self.basis.reservations.charges if item.decision_id == self.basis.seed.decision_id)
        require({item.request_sha256 for item in previous} == {item.request_sha256 for item in charges},
                'context_previous_accounting')
        attempts = {item.request_sha256: item.max_attempts for item in charges}
        require(all(attempts[item.request_sha256] == item.request.planning_request.context.limits.max_attempts
                    for item in previous), 'context_previous_call_allowance')
        remaining = self.basis.remaining()
        require(min(remaining.slot_requests, remaining.campaign_requests, remaining.slot_model_calls,
                    remaining.campaign_model_calls) > 0, 'context_allowance_exhausted')
        object.__setattr__(self, 'previous', previous)

    @property
    def lineage(self):
        return SupervisionLineage(ordinal=len(self.previous) + 1,
            root_request_sha256=self.previous[0].request_sha256 if self.previous else None,
            parent_request_sha256=self.previous[-1].request_sha256 if self.previous else None)

    @property
    def engagement(self):
        identity = {'seed': self.basis.seed.sha256, 'recipe': self.basis.recipe.sha256,
                    'actor': self.planning_actor, 'lineage': self.lineage.model_dump(mode='json')}
        return EngagementRef(scope=self.basis.reference.scope,
                             engagement_id=hashlib.sha256(canonical(identity)).hexdigest())

    @property
    def deadline(self):
        return min(self.basis.deadline_unix_ms,
                   self.previous[-1].request.deadline_unix_ms if self.previous else self.basis.deadline_unix_ms)

    @property
    def limits(self):
        limits = (self.previous[-1].request.planning_request.context.limits if self.previous
                  else self.basis.recipe.document().limits)
        remaining = self.basis.remaining()
        data = limits.model_dump(mode='json')
        data['max_attempts'] = min(limits.max_attempts, remaining.slot_model_calls, remaining.campaign_model_calls)
        return type(limits).model_validate_json(canonical(data))

    @property
    def actions(self):
        return (self.previous[-1].request.planning_request.context.allowed_actions if self.previous
                else self.basis.recipe.document().allowed_actions)

    def declaration(self, policy):
        policy = ArtifactRef.model_validate_json(policy.model_dump_json())
        seed, recipe = self.basis.seed, self.basis.recipe.document()
        require(policy.scope == self.basis.reference.scope and policy.sha256 == seed.policy.sha256 and
                policy.size_bytes == len(seed.policy.canonical) and policy.media_type == 'application/json',
                'context_published_policy')
        fields = {item.port: item.value for item in seed.document().original_fields}
        permissions = tuple(CheckpointFieldContext.model_validate_json(encoded_field(field, fields[field.name]))
                            for field in self.basis.rule.fields)
        target = next(item.view.path for item in seed.footprint().observations if item.identity == seed.footprint().targets[0])
        return CheckpointContext(reference=self.basis.reference, engagement=self.engagement, lineage=self.lineage,
            checkpoint_id=self.basis.rule.checkpoint_id, checkpoint_seed_sha256=seed.sha256, recipe_sha256=self.basis.recipe.sha256,
            objective=recipe.objective, policy=policy, budget_policy=recipe.budget_policy, snapshot=seed.document().snapshot,
            target=target, fields=permissions, remaining=self.basis.remaining(), deadline_unix_ms=self.deadline,
            allowed_actions=self.actions)

    def declaration_bytes(self, policy):
        raw = encoded(self.declaration(policy))
        require(len(raw) <= 262144, 'checkpoint_context_size')
        return raw

    def frame(self, policy, declaration, *, prepared_by):
        raw = self.declaration_bytes(policy)
        declaration = ArtifactRef.model_validate_json(declaration.model_dump_json())
        require(declaration.scope == self.basis.reference.scope and declaration.sha256 == hashlib.sha256(raw).hexdigest() and
                declaration.size_bytes == len(raw) and declaration.media_type == 'application/json' and
                declaration.schema_ref == checkpoint_context_schema(), 'context_published_declaration')
        recipe = self.basis.recipe.document()
        context = ContextManifest(scope=recipe.scope, objective=recipe.objective, prompt=recipe.prompt, policy=policy,
            model=recipe.model, entries=(*recipe.entries, ContextEntry(artifact=declaration, role='constraint', required=True)),
            omissions=recipe.omissions, allowed_actions=self.actions, output_schema=checkpoint_draft_schema(), limits=self.limits)
        self.basis.recipe.require_context(context, declaration.sha256)
        original = EngagementRequest(reference=self.engagement, actor_id=self.planning_actor, purpose='supervision',
            decision_scope=declaration.sha256, runtime_cut=self.basis.seed.footprint().cut, context=context)
        request = CheckpointRequest(reference=self.basis.reference, checkpoint_id=self.basis.rule.checkpoint_id,
            policy=policy, snapshot=self.basis.seed.document().snapshot, planning_request=original,
            planning_request_sha256=hashlib.sha256(encoded(original)).hexdigest(),
            deadline_unix_ms=self.deadline, lineage=self.lineage)
        frame = CheckpointFrame.capture(request, self.basis.seed.footprint(), prepared_by=prepared_by,
                                        planning_actor=self.planning_actor)
        RequestSeries((*self.previous, frame))
        return frame


def encoded_field(field, value):
    return canonical({'name': field.name, 'value_type': field.value_type.model_dump(mode='json'),
        'constraint': field.constraint.model_dump(mode='json'), 'original_value': value.model_dump(mode='json'),
        'original_value_sha256': scalar_digest(value)})
