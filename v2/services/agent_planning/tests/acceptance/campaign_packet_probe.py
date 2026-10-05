"""Actual public peer inputs to exact packet and owned preparation journal."""

import importlib.util
import json
import os
import sys
from importlib.metadata import version
from pathlib import Path

from amphora_agent_planning.access import Principal
from amphora_agent_planning.campaign_artifact_context import (
    CampaignArtifactContextReader,
)
from amphora_agent_planning.campaign_context import ResearchSelection
from amphora_agent_planning.campaign_knowledge_access import (
    CampaignGraphSelection,
    CampaignKnowledgeReader,
)
from amphora_agent_planning.campaign_packet import prepare
from amphora_agent_planning.campaign_preparations.journal import (
    CampaignPreparationJournal,
)
from amphora_agent_planning.campaign_research_access import (
    CampaignResearchTransport,
    ResearchRecordReader,
)
from amphora_agent_planning.campaign_slice_plan import CampaignSlicePlan
from amphora_agent_planning.context import RequestSnapshot
from amphora_agent_planning.graph_context import GraphPins
from amphora_agent_planning.knowledge_access import KnowledgeTransport
from amphora_agent_planning.metadata_reads import MetadataTransport
from amphora_agent_planning.persistence.journal import PlanningJournal
from amphora_agent_planning.registry_access import DiscoveryQuery, RegistryReader
from amphora_agent_planning.research_view_access import (
    ResearchViewReader,
    ResearchViewTransport,
    ResearchViewWindow,
    ViewSelection,
)
from amphora_agent_planning.retrieval_access import RetrievalReader, RetrievalSelection
from amphora_agent_planning.runtime_metadata import RuntimeMetadataReader
from amphora_agent_planning.source_access import DataReader
from amphora_contracts_core import Scope
from amphora_contracts_knowledge import (
    AssertionRevisionRef,
    DomainGraphRef,
    DomainHead,
    EntityRevisionRef,
    StructuralPolicyRef,
    VocabularyRef,
)
from amphora_contracts_representations import RetrieveRepresentations
from amphora_contracts_research_views import (
    ObservationSeriesRequest,
    PropertyViewRequest,
    SpecimenViewRequest,
)
from amphora_contracts_tools import LockEntry
from sqlalchemy import create_engine


def wire(model, value):
    return model.model_validate_json(json.dumps(value))


def summary(stored):
    if stored is None:
        return None
    return {'manifest_sha256': stored.record.sha256, 'packet_sha256': stored.record.document().packet.sha256,
        'registered_at': stored.registered_at.isoformat(), 'plan_sha256': stored.record.document().plan_sha256}


def assemble(value, request):
    endpoints = json.loads(os.environ['CTX_ENDPOINTS'])
    token = os.environ['CTX_READ_TOKEN']
    artifacts = CampaignArtifactContextReader(DataReader(endpoints['data'], token)).read(request).projection
    plan = CampaignSlicePlan.from_artifacts(artifacts)
    registry = RegistryReader(MetadataTransport('registry', endpoints['registry'], token))
    inventory = registry.discover(DiscoveryQuery(request, limit=1))
    exact = registry.exact(request, wire(LockEntry, value['lock']))
    plan = plan.with_registry(inventory, (exact,))
    runtime = RuntimeMetadataReader(MetadataTransport('runtime', endpoints['runtime'], token))
    universe = runtime.universe(request, expected=value['universe']['universe_sha256'])
    schemas = runtime.schemas(universe, universe.document().schemas)
    plan = plan.with_runtime(schemas)
    graph = value['graph']
    pins = GraphPins(wire(DomainGraphRef, graph['graph']), wire(DomainHead, graph['base']),
        wire(VocabularyRef, graph['vocabulary']), wire(StructuralPolicyRef, graph['policy']))
    selected = CampaignGraphSelection.bind(request, pins, tuple(wire(EntityRevisionRef, ref) for ref in graph['entities']),
        tuple(wire(AssertionRevisionRef, ref) for ref in graph['assertions']))
    knowledge = CampaignKnowledgeReader(KnowledgeTransport(endpoints['knowledge'], token)).read(selected)
    plan = plan.with_graph(knowledge)
    selection = ResearchSelection.from_bytes(json.dumps(value['selection']).encode(), request)
    research_token = os.environ.get('CTX_RESEARCH_TOKEN', token)
    records = ResearchRecordReader(CampaignResearchTransport(endpoints['research'], research_token)).review(selection)
    views, properties = [], None
    reader, window = ResearchViewReader(ResearchViewTransport(endpoints['research'], research_token)), ResearchViewWindow()
    for name, model in (('specimens', SpecimenViewRequest), ('properties', PropertyViewRequest), ('observation_series', ObservationSeriesRequest)):
        result = reader.read(ViewSelection.bind(wire(model, value['queries'][name]), request), window)
        views.append(result)
        if name == 'properties' and result.page is not None:
            properties = result.page.document().model_dump(mode='json')['rows'][0]['value']
    plan = plan.with_research(records.context, tuple(views))
    query = RetrievalSelection.bind(request, wire(RetrieveRepresentations, value['query']), value['result_sha256'])
    retrieved = RetrievalReader(MetadataTransport('data', endpoints['data'], token)).read(query)
    plan = plan.with_retrieval(retrieved)
    details = {'artifact_failures': [item.failure for item in artifacts.items if item.failure is not None],
        'root_hashes': [item.planned.reference.sha256 for item in artifacts.items if item.body is not None and
                       set(item.planned.roles) & {'objective', 'prompt', 'policy', 'model_configuration'}],
        'registry_count': len(inventory.records), 'runtime_schemas': len(schemas.records), 'runtime_failures': len(schemas.failures),
        'graph_failure': knowledge.failure, 'graph_retracted': [] if knowledge.context is None else
            sorted(ref.assertion_id for ref in knowledge.context.index().retracted),
        'research_records': len(records.context.records), 'research_gaps': [gap.reason for gap in records.context.gaps],
        'assessment_dispositions': [row.document().outcome.assessment.disposition for row in records.context.records if row.identity.kind == 'assessment'],
        'view_failures': [page.failure for page in views], 'properties_value': properties, 'retrieval_failure': retrieved.failure}
    return plan, details


def run(path):
    assert version('amphora-agent-planning') == '0.49.0'
    assert all(importlib.util.find_spec(name) is None for name in (
        'amphora_research', 'amphora_knowledge', 'amphora_data_artifacts', 'amphora_campaign_runtime', 'amphora_capability_registry', 'fastapi'))
    value = json.loads(path.read_bytes())
    request = RequestSnapshot.from_bytes(json.dumps(value['request']).encode(), actor_id='fixture', scope=wire(Scope, value['scope']))
    principal = Principal('fixture', request.document().reference.scope, frozenset({'record_requests', 'record_attempts', 'read_attempts'}))
    engine = create_engine(os.environ['CTX_PLANNING_DB'])
    journal = CampaignPreparationJournal(engine)
    try:
        if value.get('mode') == 'history':
            return {'pid': os.getpid(), 'stored': summary(journal.read(principal, request.document().reference))}
        plan, details = assemble(value, request)
        outcome = prepare(plan)
        result = {'pid': os.getpid(), 'request_sha256': request.sha256, **details,
            'preparation_failure': outcome.failure, 'missing_required': list(outcome.missing_required)}
        if outcome.packet is not None:
            packet = outcome.packet
            content = json.loads(packet.canonical)['untrusted_context']
            result.update(packet_sha256=packet.sha256, packet_bytes=len(packet.canonical), input_tokens=packet.fit.measurement.input_tokens,
                output_reserve=packet.fit.document()['output_reserve'], included_lanes=sorted({row['lane'] for row in content['slices']}),
                omissions=len(content['budget_omissions']), consumed=len(content['consumed_observations']))
            if value.get('mode', 'store') == 'store':
                PlanningJournal(engine).register(principal, request)
                result['stored'] = summary(journal.register(principal, plan, packet))
        if value.get('mode') == 'inspect':
            result['stored'] = summary(journal.read(principal, request.document().reference))
        return result
    finally:
        engine.dispose()


if __name__ == '__main__':
    print(json.dumps(run(Path(sys.argv[1]))))
