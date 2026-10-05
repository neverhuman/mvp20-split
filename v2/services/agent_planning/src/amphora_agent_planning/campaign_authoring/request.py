"""Exact public authoring commands; no durable origin or execution authority."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_commands import NUMERIC_ENCODING
from amphora_contracts_core import Identifier
from amphora_contracts_graph_runtime import (
    SaveDraft,
    ValidateDraft,
    parse_authoring_command,
)
from pydantic import TypeAdapter

from ..budget import BudgetPolicy
from ..campaign_context.records import canonical
from ..campaign_decisions import CampaignDecisionReview
from ..context.policy import require


@dataclass(frozen=True)
class AuthoringRequest:
    owner_id: str
    canonical: bytes

    @classmethod
    def bind(cls, owner_id, command):
        TypeAdapter(Identifier).validate_python(owner_id, strict=True)
        checked = parse_authoring_command(command.identity.command_family, command.canonical_bytes)
        require(checked == command, 'authoring_command_binding')
        expected = NUMERIC_ENCODING if checked.identity.command_family == 'definition.save' else 'amphora-command-v1'
        require(checked.profile == expected, 'authoring_command_profile')
        return cls(owner_id, checked.canonical_bytes)

    def command(self):
        value = json.loads(self.canonical)
        command = parse_authoring_command(value['identity']['command_family'], self.canonical)
        require(self.bind(self.owner_id, command) == self, 'authoring_request_canonical')
        return command

    def payload(self):
        command = self.command()
        model = SaveDraft if command.identity.command_family == 'definition.save' else ValidateDraft
        return model.model_validate_json(json.dumps(json.loads(command.canonical_bytes)['payload']))


@dataclass(frozen=True)
class AuthoringPlan:
    review: CampaignDecisionReview
    budget: BudgetPolicy
    owner_id: str
    actor_id: str

    @classmethod
    def bind(cls, review, budget, *, owner_id, actor_id):
        verified = CampaignDecisionReview.bind(review.composition.evidence.proposal, review.declaration, budget)
        require(verified == review, 'authoring_review_binding')
        require(verified.next_step == 'compile_future_draft', 'authoring_future_required')
        for value in (owner_id, actor_id):
            TypeAdapter(Identifier).validate_python(value, strict=True)
        return cls(verified, budget, owner_id, actor_id)

    def _slot(self):
        require(self.bind(self.review, self.budget, owner_id=self.owner_id, actor_id=self.actor_id) == self,
                'authoring_plan_binding')
        attempt = self.review.composition.evidence.proposal.attempt
        # Mutable generated content is deliberately excluded: a changed output
        # cannot evade the original owner's immutable command conflict.
        identity = {'format': 'planning-authoring-slot.v1', 'attempt': attempt.reference().model_dump(mode='json'),
                    'owner_id': self.owner_id, 'actor_id': self.actor_id}
        return hashlib.sha256(canonical(identity)).hexdigest()

    def _request(self, family, payload, slot):
        scope = self.review.composition.evidence.proposal.attempt.request.document().reference.scope
        envelope = {'identity': {'scope': scope.model_dump(mode='json'), 'actor_id': self.actor_id,
                    'command_family': family, 'command_id': 'planning-' + family + '-' + slot},
                    'payload': payload.model_dump(mode='json')}
        if family == 'definition.save':
            envelope['encoding'] = NUMERIC_ENCODING
        return AuthoringRequest.bind(self.owner_id, parse_authoring_command(family, canonical(envelope)))

    def save(self):
        slot = self._slot()
        candidate = self.review.composition.authored.candidate
        payload = SaveDraft(draft_id='planning-' + slot, expected_revision=0,
                            title=candidate.title, definition=candidate.definition)
        return self._request('definition.save', payload, slot)

    def validate(self, saved):
        from .outcome import AuthoringOutcome

        verified = AuthoringOutcome.bind(saved.request, saved.receipt, saved.readback)
        require(verified == saved and verified.request == self.save() and verified.status == 'saved',
                'authoring_saved_readback_required')
        head = verified.readback.head
        return self._request('definition.validate', ValidateDraft(draft_id=head.draft_id,
                             revision=head.revision, content_sha256=head.content_sha256), self._slot())
