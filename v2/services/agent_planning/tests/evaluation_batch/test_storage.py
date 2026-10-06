"""Actual own-SQL suite immutability, contention, rights and replacement."""

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_agent_planning.evaluation import EvaluationProtocol
from amphora_agent_planning.evaluation_batch import EvaluationBatch
from amphora_agent_planning.evaluation_batch.storage import EvaluationJournal
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from .test_binding import prepared

pytestmark = pytest.mark.postgres


def setup(stored):
    protocol, _, requests, policies = prepared(snapshot=stored.snapshot)
    batch = EvaluationBatch.prepare(protocol, stored.principal, requests, policies)
    return protocol, batch, EvaluationJournal(stored.engine)


def test_original_suite_replays_and_survives_replacement_without_attempts(stored):
    protocol, batch, journal = setup(stored)
    actor = stored.principal
    assert journal.read(actor, protocol.manifest.suite_id) is None
    expected = journal.register(actor, protocol, batch)
    assert journal.register(actor, protocol, batch) == expected
    replacement = create_engine(stored.engine.url)
    try:
        reader = replace(actor, actions=frozenset({'read_attempts'}))
        assert EvaluationJournal(replacement).read(reader, protocol.manifest.suite_id) == expected
    finally:
        replacement.dispose()
    with stored.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM planning.attempts WHERE tenant_id=:tenant AND project_id=:project'),
            {'tenant': actor.scope.tenant_id, 'project': actor.scope.project_id}).scalar_one() == 0
    for verb in ('UPDATE planning.evaluation_suites SET actor_id=actor_id', 'DELETE FROM planning.evaluation_suites'):
        with pytest.raises(DBAPIError), stored.engine.begin() as conn:
            conn.execute(text(verb + ' WHERE tenant_id=:tenant AND project_id=:project'),
                         {'tenant': actor.scope.tenant_id, 'project': actor.scope.project_id})


def test_competing_registration_has_one_immutable_protocol(stored):
    protocol, batch, journal = setup(stored)
    barrier = Barrier(2)
    def register():
        barrier.wait(5)
        return journal.register(stored.principal, protocol, batch)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(register) for _ in range(2)]
        assert futures[0].result(10) == futures[1].result(10) == (protocol, batch)
    changed = protocol.manifest.model_dump(mode='json')
    changed['categories'][0]['minimum_score'] = 1
    altered = EvaluationProtocol.load(json.dumps(changed).encode(), protocol.corpus_bytes)
    inputs = {'reference': batch.tasks[0].original}
    policies = {'reference': batch.tasks[0].policy}
    altered_batch = EvaluationBatch.prepare(altered, stored.principal, inputs, policies)
    with pytest.raises(ValueError, match='evaluation_suite_conflict'):
        journal.register(stored.principal, altered, altered_batch)
    assert journal.read(stored.principal, protocol.manifest.suite_id) == (protocol, batch)


def test_scoped_grants_actor_binding_and_changed_batch_fail_closed(stored):
    protocol, batch, journal = setup(stored)
    actor = stored.principal
    journal.register(actor, protocol, batch)
    reader = replace(actor, actions=frozenset({'read_attempts'}))
    with pytest.raises(PermissionError):
        journal.register(reader, protocol, batch)
    with pytest.raises(PermissionError):
        journal.read(replace(actor, actions=frozenset()), protocol.manifest.suite_id)
    with pytest.raises(ValueError, match='evaluation_actor_mismatch'):
        journal.read(replace(reader, actor_id='foreign'), protocol.manifest.suite_id)
    foreign = replace(reader, scope=actor.scope.model_copy(update={'project_id': 'unknown-project'}))
    assert journal.read(foreign, protocol.manifest.suite_id) is None
    with pytest.raises(ValueError, match='evaluation_batch_conflict'):
        journal.register(actor, protocol, replace(batch, accounting_units=0))
