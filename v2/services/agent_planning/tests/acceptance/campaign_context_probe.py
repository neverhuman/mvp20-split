"""Planning-only public clients; input/output JSON, no peer implementation or SQL."""

import hashlib
import importlib.util
import json
import os
import sys
from importlib.metadata import version
from pathlib import Path

from amphora_agent_planning.campaign_data_access import (
    ArtifactSelection,
    CampaignArtifactReader,
)
from amphora_agent_planning.campaign_knowledge_access import (
    CampaignGraphSelection,
    CampaignKnowledgeReader,
)
from amphora_agent_planning.context import RequestSnapshot
from amphora_agent_planning.graph_context import GraphPins
from amphora_agent_planning.knowledge_access import KnowledgeTransport
from amphora_agent_planning.metadata_reads import MetadataTransport
from amphora_agent_planning.registry_access import DiscoveryQuery, RegistryReader
from amphora_agent_planning.retrieval_access import RetrievalReader, RetrievalSelection
from amphora_agent_planning.runtime_metadata import RuntimeMetadataReader
from amphora_agent_planning.source_access import DataReader
from amphora_contracts_core import ArtifactRef, Scope
from amphora_contracts_knowledge import (
    AssertionRevisionRef,
    DomainGraphRef,
    DomainHead,
    EntityRevisionRef,
    StructuralPolicyRef,
    VocabularyRef,
)
from amphora_contracts_representations import RetrieveRepresentations
from amphora_contracts_tools import LockEntry


def wire(model, value):
    return model.model_validate_json(json.dumps(value))


def main():
    assert version('amphora-agent-planning') == '0.39.0'
    assert all(importlib.util.find_spec(name) is None for name in (
        'amphora_research', 'amphora_knowledge', 'amphora_campaign_runtime', 'amphora_capability_registry', 'amphora_data_artifacts'))
    value = json.loads(Path(sys.argv[1]).read_bytes())
    endpoints = json.loads(os.environ['CTX_ENDPOINTS'])
    token = os.environ['CTX_READ_TOKEN']
    request = RequestSnapshot.from_bytes(json.dumps(value['request']).encode(), actor_id='fixture', scope=wire(Scope, value['scope']))
    result = {'pid': os.getpid(), 'request': request.sha256}
    registry = RegistryReader(MetadataTransport('registry', endpoints['registry'], token))
    scan = registry.discover(DiscoveryQuery(request, limit=1))
    result['registry'] = {'failure': scan.failure, 'complete': scan.complete, 'count': len(scan.records)}
    try:
        exact = registry.exact(request, wire(LockEntry, value['lock']))
        result['registry']['exact'] = hashlib.sha256(exact.canonical).hexdigest()
    except ValueError as error:
        result['registry']['exact_failure'] = str(error)
    runtime = RuntimeMetadataReader(MetadataTransport('runtime', endpoints['runtime'], token))
    try:
        universe = runtime.universe(request, expected=value['universe']['universe_sha256'])
        schemas = runtime.schemas(universe, universe.document().schemas)
        result['runtime'] = {'universe': universe.sha256, 'schemas': [hashlib.sha256(row.body).hexdigest() for row in schemas.records],
            'failures': [row.code for row in schemas.failures]}
    except ValueError as error:
        result['runtime'] = {'failure': str(error)}
    artifacts = CampaignArtifactReader(DataReader(endpoints['data'], token)).read(
        ArtifactSelection.bind(request, tuple(wire(ArtifactRef, ref) for ref in value['artifacts'])))
    result['artifacts'] = {'bodies': [hashlib.sha256(row.body).hexdigest() for row in artifacts.records],
        'failures': [row.code for row in artifacts.failures], 'selection': artifacts.selection.sha256}
    query = RetrievalSelection.bind(request, wire(RetrieveRepresentations, value['query']), value['result_sha256'])
    retrieval = RetrievalReader(MetadataTransport('data', endpoints['data'], token)).read(query)
    result['retrieval'] = {'failure': retrieval.failure, 'selection': retrieval.selection.sha256,
        'record': None if retrieval.record is None else json.loads(retrieval.record.canonical)}
    graph = value['graph']
    pins = GraphPins(wire(DomainGraphRef, graph['graph']), wire(DomainHead, graph['base']),
        wire(VocabularyRef, graph['vocabulary']), wire(StructuralPolicyRef, graph['policy']))
    selected = CampaignGraphSelection.bind(request, pins, tuple(wire(EntityRevisionRef, ref) for ref in graph['entities']),
        tuple(wire(AssertionRevisionRef, ref) for ref in graph['assertions']))
    knowledge = CampaignKnowledgeReader(KnowledgeTransport(endpoints['knowledge'], token)).read(selected)
    result['knowledge'] = {'failure': knowledge.failure, 'selection': knowledge.selection.sha256,
        'snapshot': None if knowledge.context is None else hashlib.sha256(knowledge.context.snapshot_bytes).hexdigest(),
        'retracted': [] if knowledge.context is None else sorted(ref.assertion_id for ref in knowledge.context.index().retracted)}
    print(json.dumps(result))


if __name__ == '__main__':
    main()
