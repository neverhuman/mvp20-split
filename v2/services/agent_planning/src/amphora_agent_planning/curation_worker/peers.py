"""Public owner clients only; construction makes no network or model calls."""
import os
from dataclasses import dataclass

from amphora_tool_protocol import ArtifactClient, WorkerIdentity

from ..campaign_artifact_context import CampaignArtifactContextReader
from ..capability_acceptance.collection import AcceptanceCollector
from ..campaign_data_access import CampaignArtifactReader
from ..campaign_exchanges import RegistryEligibilityClient, RuntimeAuthoringClient
from ..campaign_refresh import RefreshCollector
from ..campaign_research_access import ResearchRecordReader
from ..campaign_research_access.transport import CampaignResearchTransport
from ..curation_declaration.workflow import DeclarationTransport
from ..curation_knowledge import CurationKnowledgeReader
from ..curation_preparation import CurationContextAssembler
from ..curation_runtime import CurationRuntimeReader
from ..knowledge_access.transport import KnowledgeTransport
from ..metadata_reads.transport import MetadataTransport
from ..registry_access import RegistryReader
from ..runtime_metadata import RuntimeMetadataReader
from ..source_access.transport import DataReader


@dataclass(frozen=True)
class CurationPeers:
    data: DataReader
    artifacts: ArtifactClient
    assembler: CurationContextAssembler
    refresh: RefreshCollector
    runtime: RuntimeAuthoringClient
    registry: RegistryEligibilityClient
    acceptance: AcceptanceCollector

    @classmethod
    def bind(cls, reviewed):
        config = reviewed.configuration
        tokens = {name: os.environ[getattr(config, name).token_env]
                  for name in ('data', 'runtime', 'registry', 'knowledge', 'research')}
        data = DataReader(config.data.endpoint, tokens['data'])
        artifacts = ArtifactClient(DeclarationTransport(config.data.endpoint, tokens['data']),
            WorkerIdentity(config.actor_id, config.scope))
        runtime = MetadataTransport('runtime', config.runtime.endpoint, tokens['runtime'])
        registry = MetadataTransport('registry', config.registry.endpoint, tokens['registry'])
        research = ResearchRecordReader(CampaignResearchTransport(config.research.endpoint, tokens['research']))
        assembler = CurationContextAssembler(artifacts=CampaignArtifactContextReader(data),
            registry=RegistryReader(registry), runtime=RuntimeMetadataReader(runtime),
            knowledge=CurationKnowledgeReader(KnowledgeTransport(config.knowledge.endpoint, tokens['knowledge'])),
            research=research, originals=CurationRuntimeReader(runtime))
        refresh = RefreshCollector(artifacts=CampaignArtifactReader(data), research=research,
            registry=assembler.registry, runtime=assembler.runtime)
        return cls(data, artifacts, assembler, refresh,
            RuntimeAuthoringClient(config.runtime_owner, config.runtime_actor, config.runtime.endpoint, tokens['runtime']),
            RegistryEligibilityClient(config.eligibility.owner_id, config.eligibility.actor_id, config.registry.endpoint, tokens['registry']),
            AcceptanceCollector(registry, data))
