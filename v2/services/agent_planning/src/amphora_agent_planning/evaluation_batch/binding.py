"""No provider/SQL side effects: validate the entire conservative suite before work."""

import hashlib
from dataclasses import dataclass

from ..budget import BudgetPolicy
from ..context import AttemptBinding, RequestSnapshot
from ..context.policy import require
from ..evaluation.protocol import canonical


@dataclass(frozen=True)
class EvaluationTask:
    case_id: str
    repetition: int
    original: RequestSnapshot
    request: RequestSnapshot
    policy: BudgetPolicy

    @property
    def original_sha256(self):
        return self.original.sha256

    @property
    def binding(self):
        return AttemptBinding(self.request, 1)

    @property
    def demand(self):
        return self.policy.demand(self.binding)

    def identity(self):
        return {'case_id': self.case_id, 'repetition': self.repetition, 'original_sha256': self.original_sha256,
                'request_sha256': self.request.sha256, 'policy_sha256': self.policy.sha256}


@dataclass(frozen=True)
class EvaluationBatch:
    protocol_sha256: str
    tasks: tuple[EvaluationTask, ...]
    tokens: int
    accounting_units: int
    sha256: str

    @classmethod
    def prepare(cls, protocol, principal, requests, policies):
        principal.require('record_requests', principal.scope)
        return cls._bind(protocol, principal, requests, policies)

    @classmethod
    def _bind(cls, protocol, principal, requests, policies):
        expected = {case.case_id for case in protocol.corpus.cases}
        require(set(requests) == set(policies) == expected, 'evaluation_case_bindings')
        manifest = protocol.manifest
        allowed = {canonical(item.model_dump(mode='json')) for item in manifest.allowed_data}
        tasks = []
        retained_bytes = 0
        for case in protocol.corpus.cases:
            original = RequestSnapshot.from_bytes(requests[case.case_id].canonical,
                actor_id=principal.actor_id, scope=principal.scope)
            require(original.sha256 == case.input_sha256, 'evaluation_input_digest')
            request = original.document()
            context = request.context
            require(context.model == manifest.model and context.prompt.sha256 == manifest.prompt_sha256,
                    'evaluation_model_prompt_binding')
            require(context.limits.accounting_unit == manifest.limits.accounting_unit, 'evaluation_accounting_unit')
            for name in ('max_input_tokens', 'max_output_tokens', 'max_attempts', 'total_tokens', 'total_accounting_units'):
                require(getattr(context.limits, name) <= getattr(manifest.limits, name), 'evaluation_request_ceiling')
            artifacts = [context.objective, context.prompt, context.policy, context.model.configuration,
                         *(entry.artifact for entry in context.entries)]
            require(all(canonical(item.model_dump(mode='json')) in allowed for item in artifacts),
                    'evaluation_data_not_allowed')
            policy = BudgetPolicy.from_bytes(policies[case.case_id].canonical)
            retained_bytes += len(original.canonical) + len(policy.canonical)
            require(retained_bytes <= 16777216, 'evaluation_batch_bytes')
            for ordinal in range(1, manifest.repetitions + 1):
                identity = canonical([protocol.sha256, principal.scope.model_dump(mode='json'),
                                      principal.actor_id, case.case_id, ordinal])
                reference = request.reference.model_copy(update={
                    'engagement_id': 'evaluation-' + hashlib.sha256(identity).hexdigest()})
                limits = context.limits.model_copy(update={'max_attempts': 1})
                repeated = request.model_copy(update={'reference': reference,
                    'context': context.model_copy(update={'limits': limits})})
                snapshot = RequestSnapshot.bind(repeated, actor_id=principal.actor_id, scope=principal.scope)
                retained_bytes += len(snapshot.canonical)
                require(retained_bytes <= 16777216, 'evaluation_batch_bytes')
                tasks.append(EvaluationTask(case.case_id, ordinal, original, snapshot, policy))
        tokens = sum(task.demand.tokens for task in tasks)
        units = sum(task.demand.accounting_units for task in tasks)
        require(tokens <= manifest.limits.total_tokens, 'evaluation_total_tokens')
        require(units <= manifest.limits.total_accounting_units, 'evaluation_total_accounting')
        identity = canonical({'profile': 'planning-evaluation-batch.v1', 'protocol_sha256': protocol.sha256,
                              'tasks': [task.identity() for task in tasks]})
        return cls(protocol.sha256, tuple(tasks), tokens, units, hashlib.sha256(identity).hexdigest())
