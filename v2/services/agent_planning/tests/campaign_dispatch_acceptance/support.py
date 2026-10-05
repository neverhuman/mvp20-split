"""Independent Planning worker setup; only public peer clients and Planning-owned SQL."""

import os

from amphora_agent_planning.access import Principal
from amphora_agent_planning.campaign_data_access import CampaignArtifactReader
from amphora_agent_planning.campaign_dispatch.dispatcher import CompilerDispatcher
from amphora_agent_planning.campaign_dispatch.journal import CompilerJournal
from amphora_agent_planning.campaign_dispatch.store import CompilerStore
from amphora_agent_planning.campaign_eligibility import EligibilityConfiguration
from amphora_agent_planning.campaign_exchanges import (
    RegistryEligibilityClient,
    RuntimeAuthoringClient,
)
from amphora_agent_planning.campaign_refresh import RefreshCollector
from amphora_agent_planning.metadata_reads import MetadataTransport
from amphora_agent_planning.registry_access import RegistryReader
from amphora_agent_planning.runtime_metadata import RuntimeMetadataReader
from amphora_agent_planning.source_access import DataReader
from amphora_contracts_core import Scope


def components(case, engine, *, denied=False):
    token = os.environ['CTX_TOKEN']
    principal = Principal('fixture', Scope.model_validate(case['scope']),
                          frozenset({'record_requests', 'record_attempts', 'read_attempts'}))
    eligibility = EligibilityConfiguration.bind(owner_id='fixture-registry', actor_id='fixture',
        policy_sha256=case['policy_sha256'], maximum_age_seconds=60)
    store = CompilerStore(engine, 'fixture-runtime', 'fixture', eligibility)
    journal = CompilerJournal(store)
    registry = RegistryReader(MetadataTransport('registry', os.environ['DISPATCH_REGISTRY'], token))
    runtime = RuntimeMetadataReader(MetadataTransport('runtime', os.environ['DISPATCH_RUNTIME'], token))
    refresh = RefreshCollector(artifacts=CampaignArtifactReader(DataReader(os.environ['DISPATCH_DATA'],
        os.environ['CTX_DENIED'] if denied else token)), research=None, registry=registry, runtime=runtime)
    dispatcher = CompilerDispatcher(journal, refresh,
        RuntimeAuthoringClient('fixture-runtime', 'fixture', os.environ['DISPATCH_RUNTIME'], token),
        RegistryEligibilityClient('fixture-registry', 'fixture', os.environ['DISPATCH_REGISTRY'], token))
    return principal, store, journal, dispatcher, registry, runtime
