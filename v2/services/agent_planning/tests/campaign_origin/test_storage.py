"""Owned PostgreSQL lookup, atomic observation and replacement reads."""

from dataclasses import replace

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from amphora_agent_planning.campaign_origin.index import OriginIndex, OriginPointer
from amphora_agent_planning.campaign_context.records import canonical
from amphora_agent_planning.campaign_origin.reader import CampaignOriginReader, OriginBackfill
from amphora_contracts_planning import CampaignOriginDraft

from ..campaign_authoring.test_values import saved
from ..campaign_dispatch_storage.support import setup
from ..campaign_dispatch_storage.test_journal import observed

pytestmark = pytest.mark.postgres


def prepared(stored):
    store, journal, lease, authoring = setup(stored)
    operation = journal.prepare_save(stored.principal, lease)
    accepted = saved(authoring)
    head = accepted.readback.head
    draft = CampaignOriginDraft(scope=accepted.readback.scope, draft_id=head.draft_id,
                               revision=head.revision, content_sha256=head.content_sha256)
    viewer = replace(stored.principal, actor_id='distinct-viewer', actions=frozenset({'read_campaign_origin'}))
    return store, journal, lease, operation, accepted, draft, viewer


def test_pending_absent_saved_replay_and_independent_reader(stored):
    store, journal, lease, operation, accepted, draft, viewer = prepared(stored)
    reader = CampaignOriginReader(stored.engine)
    assert reader.read(viewer, draft) is None
    terminal = observed(journal, stored.principal, lease, operation, accepted.receipt, accepted.readback)
    first = reader.read(viewer, draft)
    assert first.document().origin.proposal.actor_id == stored.principal.actor_id != viewer.actor_id
    assert first.document().origin.save.receipt == accepted.receipt
    replay = journal.append(stored.principal, lease, operation.effect.effect_id,
                            terminal.progress.position - 1, terminal.events[-1].event)
    assert replay == terminal and reader.read(viewer, draft) == first
    store.release(stored.principal, lease)
    replacement = create_engine(stored.engine.url)
    try:
        assert CampaignOriginReader(replacement).read(viewer, draft) == first
    finally:
        replacement.dispose()
    with pytest.raises(ValueError, match='origin_draft_mismatch'):
        reader.read(viewer, draft.model_copy(update={'content_sha256': 'f' * 64}))
    assert reader.read(viewer, draft.model_copy(update={'revision': 2})) is None


def test_denial_precedes_database_contact(stored):
    _, _, _, _, _, draft, viewer = prepared(stored)
    reader = CampaignOriginReader(None)
    with pytest.raises(PermissionError):
        reader.read(replace(viewer, actions=frozenset({'read_attempts'})), draft)
    with pytest.raises(PermissionError):
        reader.read(viewer, draft.model_copy(update={'scope': draft.scope.model_copy(update={'project_id': 'other'})}))


def test_index_failure_rolls_back_accepted_observation(stored, monkeypatch):
    _, journal, lease, operation, accepted, draft, viewer = prepared(stored)
    original = OriginIndex.record
    def fail_after_index(connection, selection, current):
        original(connection, selection, current)
        raise ValueError('injected_failure_after_index')
    with monkeypatch.context() as patch:
        patch.setattr(OriginIndex, 'record', fail_after_index)
        with pytest.raises(ValueError, match='injected_failure_after_index'):
            observed(journal, stored.principal, lease, operation, accepted.receipt, accepted.readback)
    assert CampaignOriginReader(stored.engine).read(viewer, draft) is None
    unchanged = journal.read(stored.principal, lease.selection.effect_id, operation.effect.effect_id)
    assert unchanged == operation
    observed(journal, stored.principal, lease, operation, accepted.receipt, accepted.readback)
    assert CampaignOriginReader(stored.engine).read(viewer, draft) is not None


def test_explicit_bounded_backfill_preserves_legacy_history(stored, monkeypatch):
    _, journal, lease, operation, accepted, draft, viewer = prepared(stored)
    # Model an already-retained pre-0021 observation, without modifying history.
    with monkeypatch.context() as patch:
        patch.setattr(OriginIndex, 'record', lambda *args: None)
        terminal = observed(journal, stored.principal, lease, operation, accepted.receipt, accepted.readback)
    assert CampaignOriginReader(stored.engine).read(viewer, draft) is None
    backfill = OriginBackfill(journal)
    assert backfill.run(stored.principal, (lease.selection.effect_id,)) == 1
    first = CampaignOriginReader(stored.engine).read(viewer, draft)
    assert backfill.run(stored.principal, (lease.selection.effect_id,)) == 1
    assert CampaignOriginReader(stored.engine).read(viewer, draft) == first
    assert journal.read(stored.principal, lease.selection.effect_id, operation.effect.effect_id) == terminal
    with pytest.raises(PermissionError):
        backfill.run(viewer, (lease.selection.effect_id,))
    for invalid in ((), ('x',) * 65, ('x', 'x')):
        with pytest.raises(ValueError, match='origin_backfill_selection_limit'):
            backfill.run(stored.principal, invalid)


def test_service_cannot_rewrite_or_delete_projection(stored):
    prepared(stored)
    for action in ('DELETE FROM', 'UPDATE'):
        sql = ('DELETE FROM planning.campaign_origins WHERE false' if action == 'DELETE FROM'
               else "UPDATE planning.campaign_origins SET content_sha256=repeat('a',64) WHERE false")
        with pytest.raises(DBAPIError):
            with stored.engine.begin() as connection:
                connection.execute(text(sql))


@pytest.mark.parametrize('corruption', ['pointer_digest', 'actor', 'effect_digest'])
def test_corrupt_lookup_cannot_claim_an_unrelated_origin(stored, monkeypatch, corruption):
    _, journal, lease, operation, accepted, draft, viewer = prepared(stored)
    with monkeypatch.context() as patch:
        patch.setattr(OriginIndex, 'record', lambda *args: None)
        terminal = observed(journal, stored.principal, lease, operation, accepted.receipt, accepted.readback)
    pointer = OriginPointer.bind(lease.selection, terminal)
    body = pointer.document().model_dump(mode='json')
    if corruption == 'actor':
        body['actor_id'] = 'unrelated-producer'
    elif corruption == 'effect_digest':
        body['effect_sha256'] = '0' * 64
    forged = OriginPointer.restore(canonical(body))
    value = forged.document()
    params = OriginIndex.key(draft) | {'content': draft.content_sha256,
        'selection': value.selection_id, 'effect': value.effect_id,
        'hash': '0' * 64 if corruption == 'pointer_digest' else forged.sha256, 'body': forged.canonical}
    with stored.engine.begin() as connection:
        connection.execute(text('INSERT INTO planning.campaign_origins '
            '(tenant_id,project_id,draft_id,revision,content_sha256,selection_id,effect_id,pointer_sha256,pointer_bytes) '
            'VALUES (:tenant,:project,:draft,:revision,:content,:selection,:effect,:hash,:body)'), params)
    expected = 'origin_index_corrupt' if corruption == 'pointer_digest' else 'origin_history_conflict'
    with pytest.raises(ValueError, match=expected):
        CampaignOriginReader(stored.engine).read(viewer, draft)
    with pytest.raises(ValueError, match='origin_index_corrupt|origin_association_conflict'):
        OriginBackfill(journal).run(stored.principal, (lease.selection.effect_id,))
    assert journal.read(stored.principal, lease.selection.effect_id, operation.effect.effect_id) == terminal


def test_unknown_or_pending_backfill_does_not_invent_origin(stored):
    _, journal, lease, _, _, draft, viewer = prepared(stored)
    assert OriginBackfill(journal).run(stored.principal, (lease.selection.effect_id,)) == 0
    assert CampaignOriginReader(stored.engine).read(viewer, draft) is None
    with pytest.raises(ValueError, match='origin_history_selection'):
        OriginBackfill(journal).run(stored.principal, ('unknown-selection',))
