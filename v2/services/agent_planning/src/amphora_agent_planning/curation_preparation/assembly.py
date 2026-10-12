"""Compose existing bounded readers; no SQL, model call, or graph mutation."""
from dataclasses import dataclass
import json

from pydantic import ValidationError
from ..curation_context import CurationIntent
from ..campaign_context import ResearchSelection
from ..campaign_context.records import canonical
from ..campaign_slice_plan import CampaignSlicePlan
from ..campaign_packet import prepare
from ..metadata_reads import MetadataWindow
from ..registry_access import DiscoveryQuery
from ..runtime_metadata.reader import PEER_CODES


@dataclass(frozen=True)
class CurationAssembly:
    plan: CampaignSlicePlan

    def prepare(self):
        return prepare(self.plan)


class CurationContextAssembler:
    def __init__(self, *, artifacts, registry, runtime, knowledge, research, originals):
        self.artifacts, self.registry, self.runtime = artifacts, registry, runtime
        self.knowledge, self.research, self.originals = knowledge, research, originals

    def read(self, intent):
        intent = CurationIntent.from_payload(intent.request, json.loads(intent.canonical))
        request = intent.request
        original = self.originals.read(intent)
        artifacts = self.artifacts.read(request)
        plan = (CampaignSlicePlan.from_artifacts(artifacts.projection)
                .with_curation(intent).with_curation_runtime(original))
        # Required source denial blocks preparation and avoids unrelated extra I/O.
        if plan.missing_required:
            return CurationAssembly(plan)
        inventory = self.registry.discover(DiscoveryQuery(request, limit=100, max_pages=2))
        plan = plan.with_registry(inventory)
        window = MetadataWindow('runtime')
        try:
            universe = self.runtime.universe(request, window=window)
            schemas = self.runtime.schemas(universe, universe.document().schemas, window=window)
            plan = plan.with_runtime(schemas)
        except ValueError as error:
            if isinstance(error, ValidationError):
                reason = 'runtime_context_invalid'
            elif str(error) in PEER_CODES:
                reason = str(error)
            else:
                raise
            plan = plan.with_runtime_unavailable(reason)
        plan = plan.with_curation_knowledge(self.knowledge.read(intent))
        selected = json.loads(intent.canonical)['command']['payload']['context']
        selection = ResearchSelection.from_bytes(canonical({'schema_version': '1',
            'engagement': request.document().reference.model_dump(mode='json'), 'request_sha256': request.sha256,
            'questions': selected['questions'], 'needs': selected['needs'], 'assessments': []}), request)
        research = self.research.review(selection)
        plan = plan.with_research(research.context)
        return CurationAssembly(plan)
