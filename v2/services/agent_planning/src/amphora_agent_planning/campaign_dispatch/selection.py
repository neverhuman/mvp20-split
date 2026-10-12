"""One original-attempt slot; immutable configuration cannot create another effect."""

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

from amphora_contracts_core import Digest, Identifier, WireModel
from amphora_contracts_planning import ProviderAttemptRef

from ..budget import BudgetPolicy
from ..campaign_authoring import AuthoringPlan
from ..campaign_context.records import canonical
from ..campaign_decisions import DecisionDeclaration
from ..campaign_eligibility import EligibilityConfiguration
from ..context.policy import require
from ..context.snapshot import _constant, _object


class _Origin(WireModel):
    attempt: ProviderAttemptRef
    preparation_sha256: Digest
    proposal_sha256: Digest


class _Runtime(WireModel):
    owner_id: Identifier
    actor_id: Identifier


class _Witness(WireModel):
    declaration_json: str
    budget_json: str
    eligibility_json: str


class _Selection(WireModel):
    format: Literal['planning-compiler-selection.v1'] = 'planning-compiler-selection.v1'
    actor_id: Identifier
    origin: _Origin
    runtime: _Runtime
    witness: _Witness


@dataclass(frozen=True)
class CompilerSelection:
    canonical: bytes

    @classmethod
    def bind(cls, principal, authoring, eligibility):
        principal.require('record_attempts', authoring.review.composition.evidence.proposal.attempt.reference().engagement.scope)
        return cls._bind(principal, authoring, eligibility)

    @classmethod
    def _bind(cls, principal, authoring, eligibility):
        checked = AuthoringPlan.bind(authoring.review, authoring.budget, owner_id=authoring.owner_id, actor_id=authoring.actor_id)
        require(checked == authoring, 'compiler_selection_authoring')
        eligibility.verify()
        proposal = checked.review.composition.evidence.proposal
        attempt = proposal.attempt.reference()
        principal.require('read_attempts', attempt.engagement.scope)
        require(principal.actor_id == proposal.attempt.request.document().actor_id, 'compiler_selection_actor')
        origin = _Origin(attempt=attempt, preparation_sha256=proposal.inputs.preparation.sha256, proposal_sha256=proposal.sha256)
        runtime = _Runtime(owner_id=checked.owner_id, actor_id=checked.actor_id)
        witness = _Witness(declaration_json=checked.review.declaration.canonical.decode(), budget_json=checked.budget.canonical.decode(),
                           eligibility_json=eligibility.canonical.decode())
        value = cls(canonical(_Selection(actor_id=principal.actor_id, origin=origin, runtime=runtime, witness=witness).model_dump(mode='json')))
        return cls.restore(value.canonical, principal)

    @classmethod
    def restore(cls, raw, principal):
        require(type(raw) is bytes and 0 < len(raw) <= 131072, 'compiler_selection_size')
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
        record = _Selection.model_validate_json(json.dumps(value, allow_nan=False))
        require(canonical(record.model_dump(mode='json')) == raw, 'compiler_selection_canonical')
        principal.require('read_attempts', record.origin.attempt.engagement.scope)
        require(record.actor_id == principal.actor_id, 'compiler_selection_actor')
        declaration = DecisionDeclaration.from_bytes(record.witness.declaration_json.encode())
        budget = BudgetPolicy.from_bytes(record.witness.budget_json.encode())
        eligibility = EligibilityConfiguration(record.witness.eligibility_json.encode())
        eligibility.verify()
        require(declaration.canonical.decode() == record.witness.declaration_json and
                budget.canonical.decode() == record.witness.budget_json, 'compiler_selection_witness_canonical')
        require(declaration.document().engagement == record.origin.attempt.engagement and
                budget.document().prompt.scope == record.origin.attempt.engagement.scope, 'compiler_selection_witness_scope')
        return cls(raw)

    def document(self):
        return _Selection.model_validate_json(self.canonical)

    def verify_origin(self, principal, authoring, eligibility):
        require(self._bind(principal, authoring, eligibility) == self, 'compiler_selection_origin')
        return self

    @property
    def effect_id(self):
        value = self.document()
        # Configuration and generated payload deliberately do not discriminate
        # the durable slot. The future journal rejects changed slot contents.
        return self.identity_for(value.actor_id, value.origin.attempt)

    @staticmethod
    def identity_for(actor_id, attempt):
        from amphora_contracts_core import Identifier
        from pydantic import TypeAdapter
        actor_id = TypeAdapter(Identifier).validate_python(actor_id, strict=True)
        attempt = ProviderAttemptRef.model_validate_json(attempt.model_dump_json())
        slot = {'format': 'planning-compiler-effect.v1', 'actor_id': actor_id,
                'attempt': attempt.model_dump(mode='json')}
        return 'compiler-' + hashlib.sha256(canonical(slot)).hexdigest()

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()
