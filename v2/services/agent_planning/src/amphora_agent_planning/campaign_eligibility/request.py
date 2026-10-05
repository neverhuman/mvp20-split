"""Finite selected release checks; generated text cannot choose policy or ports."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_commands import CanonicalCommand
from amphora_contracts_core import Identifier
from amphora_contracts_tools import ResolveRelease, parse_registry_command
from pydantic import TypeAdapter

from ..budget import BudgetPolicy
from ..campaign_context.records import canonical
from ..campaign_decisions import CampaignDecisionReview
from ..context import AttemptBinding
from ..context.policy import require
from ..registry_access import ObservedRelease
from .configuration import EligibilityConfiguration


@dataclass(frozen=True)
class EligibilityRequest:
    configuration: EligibilityConfiguration
    check_id: str
    attempt: AttemptBinding
    selected: ObservedRelease
    context: str
    command: CanonicalCommand

    @classmethod
    def bind(cls, configuration, check_id, attempt, selected, context):
        config = configuration.verify()
        for value in (check_id, context):
            TypeAdapter(Identifier).validate_python(value, strict=True)
        record = selected.document()
        scope = attempt.reference().engagement.scope
        require(ObservedRelease.bind(record, scope) == selected, 'eligibility_release_binding')
        require(context in record.descriptor.tool.applicability, 'eligibility_context')
        slot = {'format': 'planning-eligibility-slot.v1', 'attempt': attempt.reference().model_dump(mode='json'),
                'owner_id': config.owner_id, 'actor_id': config.actor_id, 'check_id': check_id,
                'tool': record.lock.tool.model_dump(mode='json')}
        identifier = 'planning-eligibility-' + hashlib.sha256(canonical(slot)).hexdigest()
        payload = ResolveRelease(release=record.lock, context=context, inputs=record.descriptor.tool.inputs,
                                 outputs=record.descriptor.tool.outputs)
        envelope = {'identity': {'scope': scope.model_dump(mode='json'), 'actor_id': config.actor_id,
                    'command_family': 'registry.resolve', 'command_id': identifier},
                    'payload': payload.model_dump(mode='json')}
        command = parse_registry_command('registry.resolve', canonical(envelope))
        return cls(configuration, check_id, attempt, selected, context, command)

    def verify(self):
        require(self.bind(self.configuration, self.check_id, self.attempt, self.selected, self.context) == self,
                'eligibility_request_binding')
        return self


@dataclass(frozen=True)
class EligibilityBatch:
    review: CampaignDecisionReview
    budget: BudgetPolicy
    configuration: EligibilityConfiguration
    check_id: str
    requests: tuple[EligibilityRequest, ...]

    @classmethod
    def bind(cls, review, budget, configuration, check_id):
        verified = CampaignDecisionReview.bind(review.composition.evidence.proposal, review.declaration, budget)
        require(verified == review and verified.next_step == 'compile_future_draft', 'eligibility_review_binding')
        configuration.verify()
        TypeAdapter(Identifier).validate_python(check_id, strict=True)
        selected = {use.release.record.document().lock: use.release.record for use in review.composition.uses}
        require(len(selected) <= 64, 'eligibility_release_limit')
        attempt = review.composition.evidence.proposal.attempt
        context = review.declaration.document().eligibility_context
        requests = tuple(EligibilityRequest.bind(configuration, check_id, attempt, selected[lock], context)
                         for lock in sorted(selected, key=lambda lock: canonical(lock.model_dump(mode='json'))))
        return cls(review, budget, configuration, check_id, requests)

    def verify(self):
        require(self.bind(self.review, self.budget, self.configuration, self.check_id) == self,
                'eligibility_batch_binding')
        return self
