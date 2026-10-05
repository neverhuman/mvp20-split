"""Typed command outcomes bind exact requests and original configured policy."""

import json
from dataclasses import dataclass

from amphora_contracts_graph_runtime import (
    DraftCommandReceipt,
    DraftRevision,
    DraftValidation,
)
from amphora_contracts_tools import RegistryReceipt

from ..campaign_authoring import AuthoringOutcome, AuthoringRequest
from ..campaign_context.records import canonical
from ..campaign_decisions import DecisionDeclaration
from ..campaign_eligibility import EligibilityObservation
from ..context.policy import require
from ..context.snapshot import _constant, _object


def verify_request(selection, effect, request):
    selected, operation = selection.document(), effect.document()
    require(operation.selection_id == selection.effect_id and operation.selection_sha256 == selection.sha256,
            'compiler_observation_selection')
    expected = effect.command()
    if operation.kind == 'resolve':
        request.verify()
        require(request.configuration.canonical.decode() == selected.witness.eligibility_json and
                request.configuration.document().owner_id == operation.owner_id,
                'compiler_observation_configuration')
        require(request.attempt.reference() == selected.origin.attempt and request.check_id == operation.check_id and
                request.selected.document().lock.descriptor_sha256 == operation.descriptor_sha256,
                'compiler_observation_check')
        declaration = DecisionDeclaration.from_bytes(selected.witness.declaration_json.encode())
        require(request.context == declaration.document().eligibility_context, 'compiler_observation_context')
        command = request.command
    else:
        require(isinstance(request, AuthoringRequest) and request.owner_id == operation.owner_id == selected.runtime.owner_id,
                'compiler_observation_owner')
        command = request.command()
        require(command.identity.actor_id == selected.runtime.actor_id, 'compiler_observation_actor')
    require(command == expected and command.identity.scope == selected.origin.attempt.engagement.scope,
            'compiler_observation_request')


@dataclass(frozen=True)
class CompilerObservation:
    canonical: bytes
    outcome: AuthoringOutcome | EligibilityObservation

    @classmethod
    def bind(cls, selection, effect, request, receipt, readback=None):
        verify_request(selection, effect, request)
        if effect.document().kind == 'resolve':
            require(readback is None, 'compiler_observation_registry_readback')
            outcome = EligibilityObservation.bind(request, receipt)
        else:
            outcome = AuthoringOutcome.bind(request, receipt, readback)
        value = {'format': 'planning-compiler-observation.v1', 'effect_id': effect.effect_id,
                 'effect_sha256': effect.sha256, 'receipt': outcome.receipt.model_dump(mode='json'),
                 'readback': None if readback is None else readback.model_dump(mode='json')}
        raw = canonical(value)
        require(len(raw) <= 2097152, 'compiler_observation_size')
        return cls(raw, outcome)

    @classmethod
    def restore(cls, raw, selection, effect, request):
        require(type(raw) is bytes and 0 < len(raw) <= 2097152, 'compiler_observation_size')
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
        require(type(value) is dict and set(value) == {'format', 'effect_id', 'effect_sha256', 'receipt', 'readback'},
                'compiler_observation_shape')
        registry = effect.document().kind == 'resolve'
        receipt_type = RegistryReceipt if registry else DraftCommandReceipt
        receipt = receipt_type.model_validate_json(json.dumps(value['receipt'], allow_nan=False))
        readback = value['readback']
        if readback is not None:
            require(not registry, 'compiler_observation_registry_readback')
            model = DraftRevision if effect.document().kind == 'save' else DraftValidation
            readback = model.model_validate_json(json.dumps(readback, allow_nan=False))
        result = cls.bind(selection, effect, request, receipt, readback)
        require(result.canonical == raw, 'compiler_observation_binding')
        return result

    @property
    def status(self):
        return self.outcome.status
