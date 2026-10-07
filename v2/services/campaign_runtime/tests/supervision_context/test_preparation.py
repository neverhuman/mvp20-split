"""Real Runtime SQL around an explicitly scripted Artifact publication peer."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from amphora_campaign_runtime.supervision_context.preparation import ContextPreparer
from amphora_campaign_runtime.supervision_context.publication import (
    ContextPublicationAddress,
)
from amphora_contracts_supervision import CheckpointContext
from sqlalchemy import text

from ..bindings.support import MemoryArtifacts
from ..supervision_preparation.test_request_gate import counts, setup


class Publications(MemoryArtifacts):
    def __init__(self, graph, reference):
        super().__init__(reference.scope)
        self.graph, self.reference = graph, reference
        self.calls, self.after_policy = [], None
        self.check_unlocked = True

    def publish(self, address, slot, body, schema, guard):
        guard()
        # A separate connection can take the run lock while the owner call executes.
        if self.check_unlocked:
            with self.graph.env.engine.begin() as conn:
                conn.execute(text('SELECT run_id FROM runtime.runs WHERE run_id=:run FOR UPDATE NOWAIT'),
                             {'run': self.reference.run_id})
        self.calls.append((slot, address.operation('artifacts.begin_upload', slot)))
        result = self.store(body, schema)
        if slot == 'policy' and self.after_policy is not None:
            callback, self.after_policy = self.after_policy, None
            callback()
        return result


def prepared(graph, *, calls=2, followup=False):
    actor, slot, data, _ = setup(graph, calls=calls, followup=followup)
    from amphora_contracts_supervision import SupervisionRef
    reference = SupervisionRef.model_validate(data['reference'])
    artifacts = Publications(graph, reference)
    actors = {(actor.scope.tenant_id, actor.scope.project_id, actor.actor_id): 'fixture'}
    preparer = ContextPreparer(graph.env.engine, actors, artifacts)
    return actor, reference, slot, artifacts, preparer


def test_publication_outside_sql_and_original_replay_after_cancel(graph_env):
    actor, ref, slot, artifacts, preparer = prepared(graph_env)
    original = preparer.prepare(actor, ref)
    assert counts(graph_env, ref.run_id) == (1, 1, 1)
    assert [item[0] for item in artifacts.calls] == ['policy', 'declaration']
    context_ref = original.frame.request.planning_request.context.entries[-1].artifact
    context = CheckpointContext.model_validate_json(artifacts.documents[context_ref.artifact_id])
    assert context.checkpoint_seed_sha256 == slot.seed.sha256
    assert context.remaining.slot_model_calls == 2
    with graph_env.env.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.runs SET status='cancelled' WHERE run_id=:run"), {'run': ref.run_id})
    replacement = ContextPreparer(graph_env.env.engine, preparer.journal.planning_actors, artifacts)
    assert replacement.prepare(actor, ref) == original
    assert len(artifacts.calls) == 2


def test_lost_publication_reply_recovers_same_content_identity_without_charging(graph_env):
    actor, ref, _, artifacts, preparer = prepared(graph_env)

    def lose():
        raise RuntimeError('synthetic-lost-publication-reply')

    artifacts.after_policy = lose
    with pytest.raises(RuntimeError, match='synthetic-lost'):
        preparer.prepare(actor, ref)
    assert counts(graph_env, ref.run_id) == (0, 0, 0)
    original = preparer.prepare(actor, ref)
    assert artifacts.calls[0] == artifacts.calls[1]
    assert counts(graph_env, ref.run_id) == (1, 1, 1)
    assert preparer.prepare(actor, ref) == original


@pytest.mark.parametrize('relevant', [True, False])
def test_selected_change_blocks_recording_but_unrelated_cut_does_not(graph_env, relevant):
    actor, ref, _, artifacts, preparer = prepared(graph_env)

    def update():
        with graph_env.env.engine.begin() as conn:
            if relevant:
                conn.execute(text('UPDATE runtime.graph_nodes SET state=CAST(:state AS jsonb) WHERE run_id=:run'),
                             {'run': ref.run_id, 'state': '{"changed":true}'})
            conn.execute(text('UPDATE runtime.runs SET revision=revision+1 WHERE run_id=:run'), {'run': ref.run_id})

    artifacts.after_policy = update
    if relevant:
        with pytest.raises(ValueError, match='selected_observation_changed'):
            preparer.prepare(actor, ref)
        assert counts(graph_env, ref.run_id) == (0, 0, 0)
        assert len(artifacts.calls) == 1
        assert preparer.prepare(actor, ref).frame.request.snapshot.cut.revision == 1
    else:
        original = preparer.prepare(actor, ref)
        assert original.frame.request.snapshot.cut.revision == 0
        assert counts(graph_env, ref.run_id) == (1, 1, 1)


def test_repair_names_parent_and_replays_even_after_allowance_exhaustion(graph_env):
    actor, ref, _, artifacts, preparer = prepared(graph_env)
    first = preparer.prepare(actor, ref)
    parent = first.frame.request_sha256
    second = preparer.prepare(actor, ref, parent_request_sha256=parent)
    assert second.frame.request.lineage.ordinal == 2
    assert counts(graph_env, ref.run_id) == (2, 2, 2)
    assert preparer.prepare(actor, ref, parent_request_sha256=parent) == second
    calls = len(artifacts.calls)
    with pytest.raises(ValueError, match='context_allowance_exhausted'):
        preparer.prepare(actor, ref, parent_request_sha256=second.frame.request_sha256)
    assert len(artifacts.calls) == calls
    with pytest.raises(ValueError, match='context_parent_missing'):
        preparer.prepare(actor, ref, parent_request_sha256='f' * 64)


def test_concurrent_initial_preparation_returns_one_original_request(graph_env):
    actor, ref, _, artifacts, preparer = prepared(graph_env)
    artifacts.check_unlocked = False
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: preparer.prepare(actor, ref), range(2)))
    assert results[0] == results[1]
    assert counts(graph_env, ref.run_id) == (1, 1, 1)


def test_changed_content_changes_publication_identity(graph_env):
    _, ref, _, _, _ = prepared(graph_env)
    original = ContextPublicationAddress(ref, 'a' * 64)
    changed = ContextPublicationAddress(ref, 'b' * 64)
    assert original.operation('artifacts.begin_upload', 'declaration') != changed.operation('artifacts.begin_upload', 'declaration')
    assert original.operation('artifacts.begin_upload', 'declaration') != original.operation('artifacts.finalize', 'declaration')


def test_permissions_and_delegation_before_publication(graph_env):
    actor, ref, _, artifacts, preparer = prepared(graph_env)
    with pytest.raises(ValueError, match='access_denied'):
        preparer.prepare(replace(actor, actions=frozenset()), ref)
    with pytest.raises(ValueError, match='planning_delegation_unavailable'):
        ContextPreparer(graph_env.env.engine, {}, artifacts).prepare(actor, ref)
    assert artifacts.calls == []


def test_another_preparer_commits_during_publication_and_original_is_returned(graph_env):
    actor, ref, _, artifacts, preparer = prepared(graph_env)
    originals = []
    replacement = ContextPreparer(graph_env.env.engine, preparer.journal.planning_actors, artifacts)
    artifacts.after_policy = lambda: originals.append(replacement.prepare(actor, ref))
    result = preparer.prepare(actor, ref)
    assert result == originals[0]
    assert counts(graph_env, ref.run_id) == (1, 1, 1)


def test_commit_race_with_newer_unrelated_cut_returns_winning_original(graph_env, monkeypatch):
    actor, ref, _, artifacts, preparer = prepared(graph_env)
    replacement = ContextPreparer(graph_env.env.engine, preparer.journal.planning_actors, artifacts)
    original_prepare = preparer.journal.prepare
    winners = []

    def race(*args):
        with graph_env.env.engine.begin() as conn:
            conn.execute(text('UPDATE runtime.runs SET revision=revision+1 WHERE run_id=:run'), {'run': ref.run_id})
        winners.append(replacement.prepare(actor, ref))
        return original_prepare(*args)

    monkeypatch.setattr(preparer.journal, 'prepare', race)
    result = preparer.prepare(actor, ref)
    assert result == winners[0]
    assert result.frame.request.snapshot.cut.revision == 1
    assert counts(graph_env, ref.run_id) == (1, 1, 1)


def test_cancel_between_final_publication_guard_and_request_commit_stays_terminal(graph_env, monkeypatch):
    actor, ref, _, artifacts, preparer = prepared(graph_env)
    original_prepare = preparer.journal.prepare

    def cancel(*args):
        with graph_env.env.engine.begin() as conn:
            conn.execute(text("UPDATE runtime.runs SET status='cancelled' WHERE run_id=:run"), {'run': ref.run_id})
        return original_prepare(*args)

    monkeypatch.setattr(preparer.journal, 'prepare', cancel)
    with pytest.raises(ValueError, match='run_not_running'):
        preparer.prepare(actor, ref)
    assert len(artifacts.calls) == 2
    assert counts(graph_env, ref.run_id) == (0, 0, 0)
