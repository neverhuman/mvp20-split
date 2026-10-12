import hashlib
import json
from dataclasses import replace

import pytest
from amphora_contracts_graph_runtime import DraftRevision, GraphRunPageV3
from amphora_agent_planning.curation_runtime import CurationRuntimeContext, CurationRuntimeReader
from amphora_agent_planning.curation_context import CurationIntent
from amphora_agent_planning.curation_intake.commands import CurationCommand
from amphora_agent_planning.campaign_packet import prepare
from amphora_agent_planning.campaign_preparations import CampaignPreparation
from ..curation_context.test_intent import source
from ..campaign_proposals.test_authored import candidate


def case():
    plan, _, incoming = source()
    graph = candidate()['definition']
    scope = plan.request.document().reference.scope.model_dump(mode='json')
    def rescope(value):
        if isinstance(value, dict):
            if set(value) == {'tenant_id', 'project_id'}: value.update(scope)
            for item in value.values(): rescope(item)
        elif isinstance(value, list):
            for item in value: rescope(item)
    rescope(graph)
    title = 'Original synthetic structure'
    digest = hashlib.sha256(json.dumps({'profile': 'amphora-draft-content-v1', 'title': title,
        'definition': graph}, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()
    draft = DraftRevision.model_validate_json(json.dumps({'schema_version': '1', 'scope': scope,
        'head': {'draft_id': 'original', 'revision': 1, 'content_sha256': digest, 'title': title},
        'parent_revision': 0, 'definition': graph}))
    run = GraphRunPageV3.model_validate_json(json.dumps({'schema_version': '3', 'scope': scope,
        'run_id': 'previous', 'plan_sha256': 'a' * 64, 'status': 'completed', 'revision': 1,
        'node_count': 200, 'budget_limit': 1000, 'reserved': 0, 'spent': 20,
        'stop_reason': None, 'nodes': [], 'next_after': None}))
    raw = json.loads(incoming.command.canonical_bytes)
    raw['payload']['context']['draft']['content_sha256'] = digest
    incoming = CurationCommand.restore(json.dumps(raw))
    intent = CurationIntent.from_template(plan.request, incoming, 'synthetic')
    return replace(plan, request=intent.request), intent, draft, run


class Peer:
    owner = 'runtime'
    def __init__(self, draft, run):
        self.draft, self.run, self.calls = draft, run, []
    def read(self, path, window):
        window.start()
        self.calls.append(path)
        result = self.run if path.startswith('/v3/') else self.draft
        window.consume(len(result.model_dump_json().encode()))
        return result


def test_original_graph_and_partial_run_summary_replay_without_mutation():
    plan, intent, draft, run = case()
    peer = Peer(draft, run)
    context = CurationRuntimeReader(peer).read(intent)
    assert peer.calls == ['/v3/graph-runs/previous?limit=1', '/v1/definition-drafts/original?revision=1']
    combined = plan.with_curation(intent).with_curation_runtime(context)
    packet = prepare(combined).packet
    assert packet is not None
    saved = CampaignPreparation.bind(combined, packet)
    assert CampaignPreparation.from_bytes(plan.request, saved.canonical, packet.canonical) == saved
    value = json.loads(context.canonical)
    assert value['draft']['definition'] == draft.definition.model_dump(mode='json')
    assert value['predecessor']['node_count'] == 200 and 'execution_summary_only' in value['limitations']
    assert 'selected_draft_not_proven_run_origin' in value['limitations']


@pytest.mark.parametrize('fault', ['draft_id', 'title', 'definition', 'run_revision', 'plan', 'active', 'blocked', 'scope'])
def test_wrong_original_or_active_campaign_rejects(fault):
    _, intent, draft, run = case()
    if fault == 'draft_id': draft = draft.model_copy(update={'head': draft.head.model_copy(update={'draft_id': 'other'})})
    if fault == 'title': draft = draft.model_copy(update={'head': draft.head.model_copy(update={'title': 'Changed'})})
    if fault == 'definition': draft = draft.model_copy(update={'definition': draft.definition.model_copy(update={'campaign_id': 'changed'})})
    if fault == 'run_revision': run = run.model_copy(update={'revision': 2})
    if fault == 'plan': run = run.model_copy(update={'plan_sha256': 'f' * 64})
    if fault == 'active': run = run.model_copy(update={'status': 'running'})
    if fault == 'blocked': run = run.model_copy(update={'status': 'blocked'})
    if fault == 'scope': run = run.model_copy(update={'scope': run.scope.model_copy(update={'project_id': 'other'})})
    with pytest.raises(ValueError): CurationRuntimeContext.bind(intent, draft, run)


def test_denied_first_read_does_not_retry_or_read_another_source():
    _, intent, draft, run = case()
    class Denied(Peer):
        def read(self, path, window):
            self.calls.append(path)
            raise ValueError('metadata_denied')
    peer = Denied(draft, run)
    with pytest.raises(ValueError, match='metadata_denied'): CurationRuntimeReader(peer).read(intent)
    assert len(peer.calls) == 1
