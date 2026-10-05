"""Reviewed universe and selected schema outcomes; no compiler or execution claim."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import SchemaRef

from ..campaign_context.records import canonical
from ..context import RequestSnapshot
from ..context.policy import require
from ..runtime_metadata import ReviewedUniverse, SchemaObservation
from ..runtime_metadata.reader import PEER_CODES


@dataclass(frozen=True)
class RuntimeContext:
    request: RequestSnapshot
    canonical: bytes

    @classmethod
    def unavailable(cls, request, reason):
        original = request.document()
        request = RequestSnapshot.bind(original, actor_id=original.actor_id, scope=original.reference.scope)
        require(original.purpose in {'campaign_proposal', 'supervision'}, 'campaign_runtime_purpose')
        require(reason in PEER_CODES | {'runtime_context_invalid'}, 'campaign_runtime_failure')
        return cls(request, canonical({'format': 'planning-campaign-runtime-context.v1', 'request_sha256': request.sha256,
            'authority': 'compiler_configuration_only', 'status': 'unavailable', 'reason': reason}))

    @classmethod
    def bind(cls, result):
        universe = ReviewedUniverse.bind(result.universe.document(), result.universe.request)
        require(type(result.selected) is tuple and len(result.selected) <= 256, 'campaign_runtime_schema_count')
        selected = tuple(SchemaRef.model_validate(ref.model_dump(mode='python', warnings=False)) for ref in result.selected)
        require(len(set(selected)) == len(selected) and all(ref in universe.document().schemas for ref in selected),
                'campaign_runtime_schema_selection')
        require(type(result.records) is tuple and type(result.failures) is tuple and
                len(result.records) + len(result.failures) == len(selected), 'campaign_runtime_schema_coverage')
        outcomes = {}
        for row in result.records:
            require(row.universe == universe, 'campaign_runtime_schema_universe')
            record = row.document()
            ref = record.reference
            require(ref in selected and ref not in outcomes, 'campaign_runtime_schema_outcome')
            verified = SchemaObservation.bind(universe, ref, record)
            require(row.body == verified.body, 'campaign_runtime_schema_bytes')
            outcomes[ref] = {'reference': ref.model_dump(mode='json'), 'status': 'available', 'record': json.loads(verified.canonical)}
        for row in result.failures:
            ref = SchemaRef.model_validate(row.reference.model_dump(mode='python', warnings=False))
            require(ref in selected and ref not in outcomes, 'campaign_runtime_schema_outcome')
            require(row.code in PEER_CODES | {'runtime_schema_invalid'}, 'campaign_runtime_failure')
            outcomes[ref] = {'reference': ref.model_dump(mode='json'), 'status': 'unavailable', 'reason': row.code}
        raw = canonical({'format': 'planning-campaign-runtime-context.v1', 'request_sha256': universe.request.sha256,
            'authority': 'compiler_configuration_only', 'status': 'available', 'universe': json.loads(universe.canonical),
            'schemas': [outcomes[ref] for ref in selected]})
        require(len(raw) <= 25165824, 'campaign_runtime_context_limit')
        return cls(universe.request, raw)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()
