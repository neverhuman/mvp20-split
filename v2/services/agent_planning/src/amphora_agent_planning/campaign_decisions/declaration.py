"""Canonical reviewed bounds are visible original inputs, never generated authority."""

import base64
import hashlib
import json
from dataclasses import dataclass

from pydantic import ValidationError

from ..campaign_context.records import canonical
from ..campaign_proposals.observations import ObservationKey
from ..context.policy import require
from ..context.snapshot import _constant, _object
from .adjustments import AdjustmentPermissions
from .wire import DECLARATION, DecisionDeclarationRecord


@dataclass(frozen=True)
class DecisionDeclaration:
    canonical: bytes

    @classmethod
    def from_bytes(cls, raw):
        require(type(raw) is bytes and 0 < len(raw) <= 65536, 'decision_declaration_size')
        try:
            value = json.loads(raw.decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
            document = DECLARATION.validate_json(json.dumps(value, allow_nan=False))
            encoded = canonical(document.model_dump(mode='json'))
        except (UnicodeError, json.JSONDecodeError, ValidationError, RecursionError) as exc:
            raise ValueError('invalid_decision_declaration') from exc
        require(len(encoded) <= 65536, 'decision_declaration_size')
        scope = document.engagement.scope
        require(document.objective.scope == scope == document.policy.scope, 'decision_declaration_scope')
        require(document.runtime_cut is None or document.runtime_cut.scope == scope, 'decision_declaration_cut_scope')
        require(len(set(document.allowed_actions)) == len(document.allowed_actions), 'decision_declaration_actions')
        require('propose_campaign' not in document.allowed_actions or document.future is not None or document.adjustments,
                'decision_declaration_candidate_scope')
        require(not document.adjustments or document.runtime_cut is not None, 'decision_declaration_adjustment_cut')
        AdjustmentPermissions.bind(document.adjustments)
        if document.future is not None:
            future = document.future
            require(len({(pin.kind, pin.identity) for pin in future.context}) == len(future.context), 'decision_context_duplicate')
            require(len(set(future.side_effects)) == len(future.side_effects), 'decision_side_effect_duplicate')
            for kind, reference in (('source', document.objective), ('policy', document.policy)):
                require(any(pin.kind == kind and pin.identity == reference.artifact_id and pin.sha256 == reference.sha256
                            for pin in future.context), 'decision_context_root_pin')
        return cls(encoded)

    def document(self):
        return DECLARATION.validate_json(self.canonical)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def bind(self, prepared):
        require(self.from_bytes(self.canonical) == self, 'decision_declaration_canonical')
        value = self.document()
        original = prepared.attempt.request.document()
        require(value.engagement == original.reference, 'decision_declaration_engagement')
        require(self.sha256 == original.decision_scope, 'decision_declaration_digest')
        require(value.objective == original.context.objective and value.policy == original.context.policy,
                'decision_declaration_roots')
        require(value.runtime_cut == original.runtime_cut, 'decision_declaration_cut')
        require(not value.adjustments or original.purpose == 'supervision', 'decision_declaration_adjustment_purpose')
        require(set(value.allowed_actions) <= set(original.context.allowed_actions), 'decision_declaration_action_scope')
        entry = self.original_entry(original, value)
        require(entry is not None and entry.role == 'constraint' and entry.required, 'decision_declaration_entry')
        require(entry.artifact.sha256 == self.sha256 and entry.artifact.size_bytes == len(self.canonical) and
                entry.artifact.media_type == 'text/plain', 'decision_declaration_artifact')
        identity = canonical(entry.artifact.model_dump(mode='json'))
        row = next((row for row in prepared.inputs.preparation.packet.context()['slices']
                    if row['lane'] == 'artifact' and canonical(row['identity']) == identity), None)
        require(row is not None and row['payload']['status'] == 'available', 'decision_declaration_unconsumed')
        require(base64.b64decode(row['payload']['body_base64'], validate=True) == self.canonical, 'decision_declaration_body')
        return ObservationKey('artifact', 'artifact', identity)

    def original_entry(self, original, value):
        """Resolve only original required input; no post-publication repinning."""
        if isinstance(value, DecisionDeclarationRecord):
            return next((entry for entry in original.context.entries
                         if entry.artifact.artifact_id == value.declaration_artifact_id), None)
        matches = [entry for entry in original.context.entries
                   if entry.role == 'constraint' and entry.required and entry.artifact.sha256 == self.sha256
                   and entry.artifact.size_bytes == len(self.canonical) and entry.artifact.media_type == 'text/plain']
        require(len(matches) == 1, 'decision_declaration_unique_entry')
        return matches[0]
