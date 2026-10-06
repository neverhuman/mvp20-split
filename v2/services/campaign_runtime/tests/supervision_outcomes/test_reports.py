"""Actual Runtime report persistence, exact replacement and authenticated socket reads."""

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from amphora_campaign_runtime.supervision_client import (
    CheckpointPlanningClient,
    ExchangeAbsent,
)
from amphora_campaign_runtime.supervision_outcomes.collection import ReportCollector
from amphora_campaign_runtime.supervision_outcomes.reports import (
    ReportJournal,
    StoredReport,
)
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from ..supervision_client.test_client import TOKEN, peer
from ..supervision_journal.test_checkpoint_storage import command, setup
from .test_reported import bind, report

__all__ = ['peer']


def prepared(graph):
    requests, frame = setup(graph)
    requests.prepare(graph.env.principal, frame, command(frame).canonical_bytes)
    return ReportJournal(requests), frame


def test_report_concurrent_registration_original_replay_and_immutable_grants(graph_env):
    journal, frame = prepared(graph_env)
    actor, ref, sha = graph_env.env.principal, frame.request.reference, frame.request_sha256
    value = bind(report(frame.request), frame.request)
    assert journal.read(actor, ref, sha) is None
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(journal.record, actor, ref, sha, value) for _ in range(2)]
        first, second = (item.result(30) for item in futures)
    assert first == second
    reader = replace(actor, actions=frozenset({'read'}))
    assert ReportJournal(journal.requests).read(reader, ref, sha) == first
    params = journal.params(actor, ref, sha)
    with graph_env.env.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.runs SET status='cancelled' WHERE tenant_id=:tenant "
            'AND project_id=:project AND run_id=:run'), params)
    assert journal.record(actor, ref, sha, value) == first
    changed = bind(report(frame.request, reason='required_artifact_unavailable'), frame.request)
    with pytest.raises(ValueError, match='execution_report_conflict'):
        journal.record(actor, ref, sha, changed)
    with pytest.raises(ValueError, match='access_denied'):
        journal.record(reader, ref, sha, value)
    with pytest.raises(ValueError, match='execution_report_observer'):
        journal.record(replace(actor, actor_id='other'), ref, sha, value)
    with pytest.raises(ValueError, match='execution_report_scope'):
        journal.read(actor, ref.model_copy(update={'scope': ref.scope.model_copy(update={'project_id': 'foreign'})}), sha)
    with pytest.raises(DBAPIError), graph_env.env.engine.begin() as conn:
        conn.execute(text('DELETE FROM runtime.supervision_execution_reports WHERE run_id=:run'), params)
    with graph_env.env.engine.connect() as conn:
        row = dict(conn.execute(text('SELECT * FROM runtime.supervision_execution_reports WHERE run_id=:run'), params).mappings().one())
    original = journal.requests.series(actor, ref.run_id, ref.decision_id)[0]
    row['report_sha256'] = 'f' * 64
    with pytest.raises(ValueError, match='stored_execution_report_corrupt'):
        StoredReport.from_row(row, original)


def test_actual_socket_read_saved_before_replacement_without_peer(graph_env, peer):
    journal, frame = prepared(graph_env)
    actor, ref, sha = graph_env.env.principal, frame.request.reference, frame.request_sha256
    client = CheckpointPlanningClient('fixture', actor.scope, peer.endpoint, TOKEN)
    collector = ReportCollector(journal, client)
    peer.status = 404
    with pytest.raises(ExchangeAbsent):
        collector.run(actor, ref, sha)
    assert journal.read(actor, ref, sha) is None
    peer.status, peer.override = 200, json.dumps(report(frame.request)).encode()
    first = collector.run(actor, ref, sha)
    assert first.report.document().attempts == ()
    count = len(peer.records)
    assert ReportCollector(journal, None).run(replace(actor, actions=frozenset({'read'})), ref, sha) == first
    assert len(peer.records) == count and all(item[0] == 'GET' for item in peer.records)
    with graph_env.env.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM runtime.supervision_winners WHERE run_id=:run'),
            {'run': ref.run_id}).scalar_one() == 0


def test_collection_requires_configured_original_actor_before_peer_read(graph_env):
    journal, frame = prepared(graph_env)
    actor, ref, sha = graph_env.env.principal, frame.request.reference, frame.request_sha256
    with pytest.raises(ValueError, match='execution_report_client'):
        ReportCollector(journal, None).run(actor, ref, sha)
    with pytest.raises(ValueError, match='execution_report_observer'):
        ReportCollector(journal, None).run(replace(actor, actor_id='foreign'), ref, sha)
    with pytest.raises(ValueError, match='supervision_request_unavailable'):
        journal.read(actor, ref, 'f' * 64)
