"""Exact derived outgoing bytes; these values alone never authorize dispatch."""

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

from amphora_contracts_core import Digest, Identifier, WireModel
from amphora_contracts_tools import parse_registry_command

from ..campaign_authoring import AuthoringRequest
from ..campaign_context.records import canonical
from ..campaign_eligibility import EligibilityBatch
from ..context.policy import require
from ..context.snapshot import _constant, _object


class _Effect(WireModel):
    format: Literal['planning-compiler-effect-payload.v1'] = 'planning-compiler-effect-payload.v1'
    selection_id: Identifier
    selection_sha256: Digest
    kind: Literal['save', 'validate', 'resolve']
    check_id: Identifier | None
    descriptor_sha256: Digest | None
    owner_id: Identifier
    command_json: str


@dataclass(frozen=True)
class CompilerEffect:
    canonical: bytes

    @classmethod
    def authoring(cls, selection, principal, authoring, eligibility, *, saved=None):
        selection.verify_origin(principal, authoring, eligibility)
        request = authoring.save() if saved is None else authoring.validate(saved)
        return cls._encode(selection, 'save' if saved is None else 'validate', request.owner_id, request.canonical)

    @classmethod
    def eligibility(cls, selection, principal, authoring, configuration, check_id, descriptor_sha256):
        selection.verify_origin(principal, authoring, configuration)
        batch = EligibilityBatch.bind(authoring.review, authoring.budget, configuration, check_id)
        matches = tuple(item for item in batch.requests if item.selected.document().lock.descriptor_sha256 == descriptor_sha256)
        require(len(matches) == 1, 'compiler_effect_selected_tool')
        request = matches[0]
        return cls._encode(selection, 'resolve', configuration.document().owner_id, request.command.canonical_bytes,
                           check_id=check_id, descriptor_sha256=descriptor_sha256)

    @classmethod
    def _encode(cls, selection, kind, owner_id, command, *, check_id=None, descriptor_sha256=None):
        record = _Effect(selection_id=selection.effect_id, selection_sha256=selection.sha256, kind=kind,
            check_id=check_id, descriptor_sha256=descriptor_sha256, owner_id=owner_id, command_json=command.decode())
        raw = canonical(record.model_dump(mode='json'))
        require(len(raw) <= 1048576, 'compiler_effect_size')
        result = cls(raw)
        result.command()
        return result

    @classmethod
    def restore(cls, raw, selection, principal, authoring, eligibility, *, saved=None):
        require(type(raw) is bytes and 0 < len(raw) <= 1048576, 'compiler_effect_size')
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
        record = _Effect.model_validate_json(json.dumps(value, allow_nan=False))
        require(canonical(record.model_dump(mode='json')) == raw, 'compiler_effect_canonical')
        if record.kind == 'resolve':
            require(saved is None, 'compiler_effect_dependency')
            result = cls.eligibility(selection, principal, authoring, eligibility, record.check_id, record.descriptor_sha256)
        else:
            require((record.kind == 'validate') == (saved is not None), 'compiler_effect_dependency')
            result = cls.authoring(selection, principal, authoring, eligibility, saved=saved)
        require(result.canonical == raw, 'compiler_effect_binding')
        return result

    def document(self):
        return _Effect.model_validate_json(self.canonical)

    def command(self):
        value = self.document()
        raw = value.command_json.encode()
        if value.kind == 'resolve':
            require(value.check_id is not None and value.descriptor_sha256 is not None, 'compiler_effect_check')
            command = parse_registry_command('registry.resolve', raw)
        else:
            require(value.check_id is None and value.descriptor_sha256 is None, 'compiler_effect_check')
            command = AuthoringRequest(value.owner_id, raw).command()
            require(command.identity.command_family == 'definition.' + value.kind, 'compiler_effect_family')
        require(command.canonical_bytes == raw, 'compiler_effect_command_canonical')
        return command

    @property
    def effect_id(self):
        value = self.document()
        slot = {'format': 'planning-compiler-operation.v1', 'selection_id': value.selection_id,
                'kind': value.kind, 'check_id': value.check_id, 'descriptor_sha256': value.descriptor_sha256}
        return 'compiler-op-' + hashlib.sha256(canonical(slot)).hexdigest()

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()
