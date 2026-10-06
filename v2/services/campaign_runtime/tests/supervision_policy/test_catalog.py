"""Configuration replacement cannot silently select another policy."""

import pytest
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_campaign_runtime.supervision_policy import ReviewedPolicy
from amphora_campaign_runtime.supervision_policy.catalog import PolicyCatalog
from amphora_contracts_core import Scope

from .support import plan, policy


def test_exact_scope_plan_and_policy_without_mutable_caller_container():
    graph = plan()
    reviewed = ReviewedPolicy.bind(graph, policy(graph))
    entries = [reviewed]
    catalog = PolicyCatalog(entries)
    entries.clear()
    scope = reviewed.document().scope
    assert catalog.require(scope, graph.sha256, reviewed.sha256) == reviewed
    for tenant, digest, policy_hash in [('other', graph.sha256, reviewed.sha256),
                                      (scope.tenant_id, 'c' * 64, reviewed.sha256),
                                      (scope.tenant_id, graph.sha256, 'c' * 64)]:
        with pytest.raises(TransitionError, match='supervision_policy_unavailable'):
            catalog.require(Scope(tenant_id=tenant, project_id=scope.project_id), digest, policy_hash)
    with pytest.raises(TransitionError, match='duplicate_reviewed_policy'):
        PolicyCatalog([reviewed, reviewed])
