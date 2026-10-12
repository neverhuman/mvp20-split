"""Original graph bytes and terminal predecessor; Runtime alone accepts successors."""
from dataclasses import dataclass
import hashlib
import json

from amphora_contracts_graph_runtime import DraftRevision, GraphRunPageV3
from ..campaign_context.records import canonical
from ..context.policy import require
from ..curation_context import CurationIntent
from ..metadata_reads import MetadataWindow


def draft_digest(draft):
    # Published amphora-draft-content-v1 authored-order profile, independent of
    # compiler plan identity. Preserve its ASCII JSON encoding exactly.
    value = {'profile': 'amphora-draft-content-v1', 'title': draft.head.title,
             'definition': draft.definition.model_dump(mode='json')}
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=True, allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class CurationRuntimeContext:
    intent: CurationIntent
    canonical: bytes

    @classmethod
    def bind(cls, intent, draft, predecessor):
        intent = CurationIntent.from_payload(intent.request, json.loads(intent.canonical))
        draft = DraftRevision.model_validate_json(draft.model_dump_json())
        predecessor = GraphRunPageV3.model_validate_json(predecessor.model_dump_json())
        original = json.loads(intent.canonical)['command']['payload']['context']
        selected, prior = original['draft'], original['predecessor']
        scope = intent.request.document().reference.scope
        require(draft.scope == scope == predecessor.scope, 'curation_runtime_scope')
        require(draft.head.draft_id == selected['draft_id'] and draft.head.revision == selected['revision']
                and draft.head.content_sha256 == selected['content_sha256'] == draft_digest(draft),
                'curation_runtime_draft_binding')
        require(predecessor.run_id == prior['run_id'] and predecessor.plan_sha256 == prior['plan_sha256']
                and predecessor.revision == prior['revision'], 'curation_runtime_predecessor_binding')
        require(predecessor.status in {'completed', 'failed', 'cancelled'}, 'curation_predecessor_active')
        require(len(predecessor.nodes) <= 1, 'curation_runtime_summary_bound')
        value = {'format': 'planning-curation-runtime.v1', 'authority': 'original_selected_context_only',
                 'curation': intent.identity, 'draft': draft.model_dump(mode='json'),
                 'predecessor': predecessor.model_dump(mode='json'),
                 'limitations': ['execution_summary_only', 'selected_draft_not_proven_run_origin',
                                 'successor_not_admitted']}
        raw = canonical(value)
        require(len(raw) <= 4194304, 'curation_runtime_context_limit')
        return cls(intent, raw)

    @classmethod
    def from_payload(cls, intent, payload):
        require(type(payload) is dict and set(payload) ==
                {'format', 'authority', 'curation', 'draft', 'predecessor', 'limitations'}, 'curation_runtime_shape')
        result = cls.bind(intent, DraftRevision.model_validate_json(canonical(payload['draft'])),
                          GraphRunPageV3.model_validate_json(canonical(payload['predecessor'])))
        require(result.canonical == canonical(payload), 'curation_runtime_payload')
        return result


class CurationRuntimeReader:
    def __init__(self, transport):
        require(transport.owner == 'runtime', 'curation_runtime_owner')
        self.transport = transport

    def read(self, intent):
        intent = CurationIntent.from_payload(intent.request, json.loads(intent.canonical))
        selected = json.loads(intent.canonical)['command']['payload']['context']
        draft, predecessor = selected['draft'], selected['predecessor']
        window = MetadataWindow('runtime', seconds=15)
        run = self.transport.read('/v3/graph-runs/' + predecessor['run_id'] + '?limit=1', window)
        record = self.transport.read('/v1/definition-drafts/' + draft['draft_id'] +
            '?revision=' + str(draft['revision']), window)
        result = CurationRuntimeContext.bind(intent, record, run)
        window.remaining()
        return result


def validate_runtime(request, slices):
    rows = [row for row in slices if row['lane'] == 'curation_runtime']
    if not rows:
        return
    intents = [row for row in slices if row['lane'] == 'curation']
    require(len(rows) == len(intents) == 1, 'curation_runtime_intent')
    intent = CurationIntent.from_payload(request, intents[0]['payload'])
    CurationRuntimeContext.from_payload(intent, rows[0]['payload'])
    require(rows[0]['identity'] == intent.identity, 'curation_runtime_identity')
