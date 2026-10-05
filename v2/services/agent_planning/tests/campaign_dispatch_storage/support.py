"""Synthetic consumed tool metadata bound before packet hashing in SQL fixtures."""

import json

from amphora_agent_planning.campaign_authoring import AuthoringPlan
from amphora_agent_planning.campaign_dispatch import CompilerSelection
from amphora_agent_planning.campaign_dispatch.journal import CompilerJournal
from amphora_agent_planning.campaign_dispatch.store import CompilerStore
from amphora_agent_planning.campaign_eligibility import EligibilityConfiguration
from amphora_agent_planning.registry_access import DiscoveryQuery, RegistryReader
from amphora_agent_planning.runtime_metadata import (
    ReviewedUniverse,
    RuntimeMetadataReader,
)
from amphora_contracts_tools import ReleasePage, ReleaseSnapshot

from ..campaign_handoff_storage.test_origin import seeded
from ..campaign_proposals.test_composition import revised_universe
from ..registry_access.test_discovery import Scripted, record


def metadata(selected):
    scope = selected.request.document().reference.scope
    value = record().model_dump(mode='json')
    value['scope'] = scope.model_dump(mode='json')
    release = ReleaseSnapshot.model_validate_json(json.dumps(value))
    scan = RegistryReader(Scripted(ReleasePage(items=(release,), next_after=None))).discover(
        DiscoveryQuery(selected.request, limit=100, max_pages=1))
    selected = selected.with_registry(scan, ())
    universe = revised_universe(lambda raw: raw.update(scope=scope.model_dump(mode='json')))
    observed = ReviewedUniverse.bind(universe, selected.request)
    return selected.with_runtime(RuntimeMetadataReader(Scripted()).schemas(observed, ()))


def setup(stored, *, tools=False):
    review, budget = seeded(stored, tools=tools, metadata_builder=metadata if tools else None)
    authoring = AuthoringPlan.bind(review, budget, owner_id='runtime', actor_id='planning-agent')
    config = EligibilityConfiguration.bind(owner_id='registry-fixture', actor_id='planning-agent', policy_sha256='e' * 64)
    selection = CompilerSelection.bind(stored.principal, authoring, config)
    store = CompilerStore(stored.engine, 'runtime', 'planning-agent', config)
    store.register(stored.principal, selection)
    return store, CompilerJournal(store), store.acquire(stored.principal, selection.effect_id, seconds=300), authoring
