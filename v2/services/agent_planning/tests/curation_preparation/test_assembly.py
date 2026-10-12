import base64
import json

from amphora_contracts_tools import ReleasePage
from amphora_agent_planning.curation_preparation import CurationContextAssembler
from amphora_agent_planning.curation_runtime import CurationRuntimeReader
from amphora_agent_planning.curation_knowledge import CurationKnowledgeReader
from amphora_agent_planning.campaign_artifact_context import CampaignArtifactContextReader
from amphora_agent_planning.campaign_research_access import ResearchRecordReader
from amphora_agent_planning.campaign_preparations import CampaignPreparation
from amphora_agent_planning.registry_access import RegistryReader
from amphora_agent_planning.runtime_metadata import RuntimeMetadataReader
from ..curation_runtime.test_context import case, Peer
from ..registry_access.test_discovery import Scripted, record
from ..runtime_metadata.test_reader import universe, schema


class Data:
    def __init__(self, plan, denied=None):
        self.bodies = {row.document()['identity']['artifact_id']:
                      base64.b64decode(row.document()['payload']['body_base64']) for row in plan.slices}
        self.denied = denied
        self.calls = []
    def artifact(self, ref, budget):
        budget.start(); self.calls.append(('metadata', ref.artifact_id))
        if ref.artifact_id == self.denied: raise ValueError('source_access_denied')
        return ref
    def content(self, ref, budget):
        budget.start(); self.calls.append(('processing', ref.artifact_id))
        body = self.bodies[ref.artifact_id]; budget.consume(len(body))
        return body


class NoReads:
    def read(self, *args):
        raise AssertionError('No selected records; peer must not be called')


def assembly(*, denied=False, runtime_denied=False):
    plan, intent, draft, run = case()
    data = Data(plan, plan.request.document().context.objective.artifact_id if denied else None)
    registry = Scripted(ReleasePage(items=(record(),), next_after=None))
    runtime = Scripted(ValueError('metadata_denied')) if runtime_denied else Scripted(
        universe(), *(schema(index) for index in range(len(universe().schemas))))
    assembler = CurationContextAssembler(artifacts=CampaignArtifactContextReader(data),
        registry=RegistryReader(registry), runtime=RuntimeMetadataReader(runtime),
        knowledge=CurationKnowledgeReader(NoReads()), research=ResearchRecordReader(NoReads()),
        originals=CurationRuntimeReader(Peer(draft, run)))
    return assembler, intent, data, registry, runtime


def test_complete_public_reader_composition_keeps_original_graph_and_inventory():
    assembler, intent, data, registry, runtime = assembly()
    result = assembler.read(intent)
    prepared = result.prepare()
    assert prepared.failure is None and prepared.packet is not None
    rows = json.loads(prepared.packet.canonical)['untrusted_context']['slices']
    lanes = {row['lane'] for row in rows}
    assert {'curation', 'curation_runtime', 'curation_knowledge', 'research', 'registry_scan',
            'registry_inventory', 'runtime', 'runtime_schema'} <= lanes
    assert len([call for call in data.calls if call[0] == 'processing']) == 4
    assert registry.paths == ['/v1/releases?limit=100']
    assert runtime.paths[0] == '/v1/definition-universe'
    saved = CampaignPreparation.bind(result.plan, prepared.packet)
    assert CampaignPreparation.from_bytes(intent.request, saved.canonical, prepared.packet.canonical) == saved


def test_required_processing_denial_stops_before_discovery_and_model_preparation():
    assembler, intent, _, registry, runtime = assembly(denied=True)
    result = assembler.read(intent)
    packet = result.prepare()
    assert packet.packet is None and packet.failure == 'required_artifact_unavailable'
    assert intent.request.document().context.objective.artifact_id in packet.missing_required
    assert not registry.paths and not runtime.paths


def test_missing_runtime_inventory_stays_visible_without_substitution():
    assembler, intent, _, _, runtime = assembly(runtime_denied=True)
    result = assembler.read(intent)
    packet = result.prepare()
    assert packet.packet is not None
    value = next(row['payload'] for row in json.loads(packet.packet.canonical)['untrusted_context']['slices']
                 if row['lane'] == 'runtime')
    assert value['status'] == 'unavailable' and value['reason'] == 'metadata_denied'
    assert len(runtime.paths) == 1


def test_selected_knowledge_and_research_gaps_survive_combined_preparation():
    from amphora_agent_planning.curation_context import CurationIntent
    from amphora_agent_planning.curation_intake.commands import CurationCommand
    from ..campaign_knowledge_access.test_reader import selected as graph_selection
    from ..campaign_context.test_records import selected as research_selection
    from ..campaign_research_access.test_reader import Peer as ResearchPeer, PATHS
    assembler, intent, _, _, _ = assembly()
    graph, knowledge_peer = graph_selection()
    research = research_selection().document()
    value = json.loads(intent.canonical)['command']
    value['payload']['context']['knowledge'] = [graph.parts()[0].base.model_dump(mode='json')]
    value['payload']['context']['questions'] = [ref.model_dump(mode='json') for ref in research.questions]
    value['payload']['context']['needs'] = [ref.model_dump(mode='json') for ref in research.needs]
    intent = CurationIntent.from_template(intent.request, CurationCommand.restore(json.dumps(value)), 'synthetic')
    research_peer = ResearchPeer()
    research_peer.values[PATHS['question']] = ValueError('research_access_denied')
    assembler.knowledge = CurationKnowledgeReader(knowledge_peer)
    assembler.research = ResearchRecordReader(research_peer)
    assembled = assembler.read(intent)
    packet = assembled.prepare()
    assert packet.failure is None
    saved = CampaignPreparation.bind(assembled.plan, packet.packet)
    assert CampaignPreparation.from_bytes(intent.request, saved.canonical, packet.packet.canonical) == saved
    rows = json.loads(packet.packet.canonical)['untrusted_context']['slices']
    assert any(row['lane'] == 'graph' and row['payload']['status'] == 'available' for row in rows)
    research_row = next(row['payload'] for row in rows if row['lane'] == 'research')
    assert len(research_peer.calls) == 2 and len(knowledge_peer.calls) == 3
    assert research_row['context']['gaps'][0]['reason'] == 'denied'
    assert len(research_row['context']['records']) == 1
