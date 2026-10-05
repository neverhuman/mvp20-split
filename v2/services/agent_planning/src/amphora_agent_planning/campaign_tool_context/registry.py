"""Bounded inventory and exact release observations, not a catalog snapshot."""

import hashlib
import json
from dataclasses import dataclass

from ..campaign_context.records import canonical
from ..context import RequestSnapshot
from ..context.policy import require
from ..registry_access import ObservedRelease
from ..registry_access.discovery import CODES


@dataclass(frozen=True)
class RegistryContext:
    request: RequestSnapshot
    canonical: bytes

    @classmethod
    def bind(cls, result, exact=()):
        query = result.query.validated()
        scope = query.request.document().reference.scope
        require(type(result.pages) is int and 0 <= result.pages <= query.max_pages and
                type(result.complete) is bool and type(result.records) is tuple and
                len(result.records) <= result.pages * query.limit, 'campaign_registry_scan_shape')
        require(result.failure is None or result.failure in CODES | {'registry_record_invalid'}, 'campaign_registry_failure')
        records = tuple(ObservedRelease.bind(row.document(), scope) for row in result.records)
        previous = query.after
        for row in records:
            record = row.document()
            digest = record.lock.descriptor_sha256
            require(previous is None or digest > previous, 'campaign_registry_order')
            require((query.capability_id is None or record.lock.tool.capability_id == query.capability_id) and
                    (query.release is None or record.lock.tool.release == query.release), 'campaign_registry_filter')
            previous = digest
        if result.complete:
            require(result.pages > 0 and result.failure is None and result.next_after is None and
                    len(records) >= (result.pages - 1) * query.limit, 'campaign_registry_completion')
        else:
            require(len(records) == result.pages * query.limit and result.next_after == previous,
                    'campaign_registry_continuation')
            require(result.failure is not None or (result.pages == query.max_pages and result.next_after is not None),
                    'campaign_registry_incomplete')
            require(result.failure is None or result.pages < query.max_pages, 'campaign_registry_failure_position')
        require(type(exact) is tuple and len(exact) <= 64, 'campaign_registry_exact_count')
        exact = tuple(ObservedRelease.bind(row.document(), scope) for row in exact)
        require(len({row.document().lock.descriptor_sha256 for row in exact}) == len(exact), 'campaign_registry_exact_duplicate')
        raw = canonical({'format': 'planning-campaign-registry-context.v1', 'authority': 'observed_inventory_only',
            'request_sha256': query.request.sha256, 'query': {'path': query.path(query.after), 'max_pages': query.max_pages},
            'complete': result.complete, 'next_after': result.next_after, 'failure': result.failure, 'pages': result.pages,
            'inventory': [json.loads(row.canonical) for row in records], 'exact': [json.loads(row.canonical) for row in exact]})
        require(len(raw) <= 33554432, 'campaign_registry_context_limit')
        return cls(query.request, raw)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()
