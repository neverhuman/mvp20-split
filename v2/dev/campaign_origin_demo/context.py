"""Actual public peer reads, fixed before deterministic proposal capture."""
import json
import os

from amphora_agent_planning.campaign_artifact_context import CampaignArtifactContextReader
from amphora_agent_planning.campaign_context import ResearchSelection
from amphora_agent_planning.campaign_knowledge_access import CampaignGraphSelection, CampaignKnowledgeReader
from amphora_agent_planning.campaign_research_access import CampaignResearchTransport, ResearchRecordReader
from amphora_agent_planning.campaign_slice_plan import CampaignSlicePlan
from amphora_agent_planning.graph_context import GraphPins
from amphora_agent_planning.knowledge_access import KnowledgeTransport
from amphora_agent_planning.metadata_reads import MetadataTransport
from amphora_agent_planning.registry_access import DiscoveryQuery, RegistryReader
from amphora_agent_planning.runtime_metadata import RuntimeMetadataReader
from amphora_agent_planning.source_access import DataReader
from amphora_contracts_knowledge import DomainGraphRef, DomainHead, VocabularyRef, StructuralPolicyRef, EntityRevisionRef, AssertionRevisionRef


def wire(model, value):
    return model.model_validate_json(json.dumps(value))


def assemble(case, request):
    endpoints = case['endpoints']
    token = lambda name: os.environ['ORIGIN_' + name.upper() + '_TOKEN']
    artifacts = CampaignArtifactContextReader(DataReader(endpoints['artifact'], token('artifact'))).read(request).projection
    assert not artifacts.missing_required, 'Required artifact processing rights/content unavailable'
    plan = CampaignSlicePlan.from_artifacts(artifacts)
    registry = RegistryReader(MetadataTransport('registry', endpoints['registry'], token('registry')))
    inventory = registry.discover(DiscoveryQuery(request, limit=100, max_pages=2))
    assert inventory.complete and inventory.records
    plan = plan.with_registry(inventory, ())
    runtime = RuntimeMetadataReader(MetadataTransport('runtime', endpoints['runtime'], token('runtime')))
    universe = runtime.universe(request)
    schemas = runtime.schemas(universe, universe.document().schemas)
    assert not schemas.failures
    plan = plan.with_runtime(schemas)
    graph = case['graph']
    pins = GraphPins(wire(DomainGraphRef, graph['graph']), wire(DomainHead, graph['base']),
                     wire(VocabularyRef, graph['vocabulary']), wire(StructuralPolicyRef, graph['policy']))
    selected = CampaignGraphSelection.bind(request, pins,
        tuple(wire(EntityRevisionRef, ref) for ref in graph['entities']),
        tuple(wire(AssertionRevisionRef, ref) for ref in graph['assertions']))
    knowledge = CampaignKnowledgeReader(KnowledgeTransport(endpoints['knowledge'], token('knowledge'))).read(selected)
    assert knowledge.failure is None and knowledge.context is not None
    plan = plan.with_graph(knowledge)
    selection = ResearchSelection.from_bytes(json.dumps({'schema_version': '1',
        'engagement': request.document().reference.model_dump(mode='json'), 'request_sha256': request.sha256,
        'questions': case['questions'], 'needs': case['needs'], 'assessments': []}).encode(), request)
    research = ResearchRecordReader(CampaignResearchTransport(endpoints['research'], token('research')))
    result = research.review(selection)
    assert not result.context.gaps and len(result.context.records) == len(case['questions']) + len(case['needs'])
    return plan.with_research(result.context), registry, runtime, research
