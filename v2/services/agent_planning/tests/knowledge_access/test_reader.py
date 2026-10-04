import hashlib
from dataclasses import replace
from datetime import datetime, timezone

import pytest
from amphora_agent_planning.extraction import ExtractionSnapshot
from amphora_agent_planning.knowledge_access import KnowledgeReader
from amphora_agent_planning.proposals.context import canonical
from amphora_agent_planning.proposals.validator import GraphCandidateValidator
from amphora_contracts_knowledge import AcceptedChangeContent, AcceptedGraphChange, ReferenceValidation

from ..proposals.support import Case


class Peer:
    def __init__(self, records):
        self.records, self.calls = records, []

    def read(self, path, reference, window):
        window.start()
        self.calls.append((path, reference))
        return self.records[path]


def inputs(history=True, scope=None):
    bound = Case(history=history, scope=scope).bind()
    task = bound.task
    records = {'/v1/graph-profiles/read': bound.knowledge.profile()}
    if history:
        snapshot = bound.knowledge.snapshot()
        proposal = GraphCandidateValidator().validate(bound.inputs).proposal().model_copy(update={'base': None, 'change_id': 'base'})
        content = AcceptedChangeContent(proposal=proposal, actor_id='fixture', policy=proposal.policy,
            validation=ReferenceValidation(checked_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                artifacts=(), sources=(), conversion_traces=(), questions=(), evidence_needs=()),
            accepted_at=datetime(2026, 1, 1, tzinfo=timezone.utc), position=1,
            resulting_snapshot=snapshot.reference, authority='structural_only')
        reference = task.document().target.base.change.model_copy(update={'sha256': hashlib.sha256(canonical(content)).hexdigest()})
        change = AcceptedGraphChange(wire_version='1', reference=reference, content=content)
        target = task.document().target.model_copy(update={'base': task.document().target.base.model_copy(update={'change': reference})})
        task = ExtractionSnapshot.from_bytes(canonical(task.document().model_copy(update={'target': target})), task.request)
        records.update({'/v1/graph-snapshots/read': snapshot, '/v1/graph-changes/read': change})
    return task, Peer(records), replace(bound.review, task=task)


def test_genesis_reads_only_profile_and_does_not_claim_reservation():
    task, peer, _ = inputs(False)
    context = KnowledgeReader(peer).review(task)
    assert context.snapshot_bytes is None
    assert [path for path, _ in peer.calls] == ['/v1/graph-profiles/read']


def test_historical_head_is_bound_without_reading_or_substituting_live_head():
    task, peer, _ = inputs()
    context = KnowledgeReader(peer).review(task)
    assert context.snapshot().reference == task.document().target.base.snapshot
    assert [path for path, _ in peer.calls] == list(peer.records)
    assert peer.calls[1][1] == task.document().target.base.snapshot
    assert peer.calls[2][1] == task.document().target.base.change


@pytest.mark.parametrize('mutation,reason', [('digest', 'knowledge_change_digest'), ('binding', 'knowledge_change_binding')])
def test_accepted_change_must_have_exact_digest_and_resulting_head(mutation, reason):
    task, peer, _ = inputs()
    change = peer.records['/v1/graph-changes/read']
    content = change.content.model_copy(update={'position': 2})
    reference = change.reference
    if mutation == 'binding':
        reference = reference.model_copy(update={'sha256': hashlib.sha256(canonical(content)).hexdigest()})
        target = task.document().target
        target = target.model_copy(update={'base': target.base.model_copy(update={'change': reference})})
        task = ExtractionSnapshot.from_bytes(canonical(task.document().model_copy(update={'target': target})), task.request)
    peer.records['/v1/graph-changes/read'] = change.model_copy(update={'reference': reference, 'content': content})
    with pytest.raises(ValueError, match=reason):
        KnowledgeReader(peer).review(task)


@pytest.mark.parametrize('group,reason', [('existing_entities', 'knowledge_selected_entity_missing'),
                                         ('existing_assertions', 'knowledge_selected_assertion_missing')])
def test_selected_references_must_exist_even_when_candidate_does_not_use_them(group, reason):
    task, peer, _ = inputs()
    refs = getattr(task.document(), group)
    field = 'entity_id' if group == 'existing_entities' else 'assertion_id'
    task = ExtractionSnapshot.from_bytes(canonical(task.document().model_copy(update={group: (*refs, refs[0].model_copy(update={field: 'absent'}))})), task.request)
    with pytest.raises(ValueError, match=reason):
        KnowledgeReader(peer).review(task)
