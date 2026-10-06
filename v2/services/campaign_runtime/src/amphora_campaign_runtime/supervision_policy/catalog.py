"""Immutable exact policy selection; no default or latest-policy fallback."""

from types import MappingProxyType

from ..lifecycle.model import TransitionError
from .policy import ReviewedPolicy


class PolicyCatalog:
    def __init__(self, policies):
        entries = {}
        for item in policies:
            policy = ReviewedPolicy.from_bytes(item.plan, item.canonical)
            record = policy.document()
            key = (record.scope.tenant_id, record.scope.project_id, record.plan_sha256, policy.sha256)
            if key in entries:
                raise TransitionError('duplicate_reviewed_policy')
            entries[key] = policy
        self._entries = MappingProxyType(entries)

    def require(self, scope, plan_sha256, policy_sha256):
        policy = self._entries.get((scope.tenant_id, scope.project_id, plan_sha256, policy_sha256))
        if policy is None:
            raise TransitionError('supervision_policy_unavailable')
        return policy
