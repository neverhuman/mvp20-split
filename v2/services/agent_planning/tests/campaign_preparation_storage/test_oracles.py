import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_agent_planning.campaign_artifact_context import (
    ArtifactContextPlan,
    ArtifactContextProjection,
)
from amphora_agent_planning.campaign_packet import prepare
from amphora_agent_planning.campaign_packet.assembly import original_artifacts
from amphora_agent_planning.campaign_preparations.journal import (
    CampaignPreparationJournal,
)
from amphora_agent_planning.campaign_slice_plan import CampaignSlicePlan
from amphora_agent_planning.context import RequestSnapshot
from amphora_agent_planning.persistence.budget import BudgetLedger
from amphora_agent_planning.persistence.dispatch import DispatchJournal
from amphora_agent_planning.persistence.journal import KEY
from amphora_agent_planning.providers import FixtureProvider, observe
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from ..persistence.test_reservations import policy

pytestmark = pytest.mark.postgres


def registered(s):
    s.requests.register(s.principal, s.plan.request)
    return s.journal.register(s.principal, s.plan, s.packet)


def alternative(s):
    selected = CampaignSlicePlan.from_artifacts(original_artifacts(s.plan)).with_runtime_unavailable('metadata_denied')
    return selected, prepare(selected).packet


@pytest.mark.parametrize('fault', ['grant', 'scope', 'actor'])
def test_read_and_write_cannot_escape_original_authority(campaign_store, fault):
    s = campaign_store
    original = registered(s)
    principal = s.principal
    error = PermissionError
    if fault == 'grant':
        principal = replace(principal, actions=frozenset())
    elif fault == 'scope':
        principal = replace(principal, scope=principal.scope.model_copy(update={'project_id': 'foreign'}))
    else:
        principal = replace(principal, actor_id='foreign')
        error = ValueError
    with pytest.raises(error):
        s.journal.read(principal, s.plan.request.document().reference)
    with pytest.raises(error):
        s.journal.register(principal, s.plan, s.packet)
    assert s.journal.read(s.principal, s.plan.request.document().reference) == original


def test_changed_observation_cannot_replace_preparation(campaign_store):
    s = campaign_store
    original = registered(s)
    selected, packet = alternative(s)
    with pytest.raises(ValueError, match='preparation_conflict'):
        s.journal.register(s.principal, selected, packet)
    assert s.journal.read(s.principal, s.plan.request.document().reference) == original


def test_same_engagement_with_changed_request_cannot_register(campaign_store):
    s = campaign_store
    s.requests.register(s.principal, s.plan.request)
    value = s.plan.request.document().model_dump(mode='json')
    value['context']['limits']['max_attempts'] = 1 if value['context']['limits']['max_attempts'] != 1 else 2
    changed = RequestSnapshot.from_bytes(json.dumps(value).encode(),
        actor_id=s.principal.actor_id, scope=s.principal.scope)
    artifacts = original_artifacts(s.plan)
    selected = CampaignSlicePlan.from_artifacts(ArtifactContextProjection.bind(ArtifactContextPlan.bind(changed), artifacts.items))
    with pytest.raises(ValueError, match='request_conflict'):
        s.journal.register(s.principal, selected, prepare(selected).packet)
    assert s.journal.read(s.principal, s.plan.request.document().reference) is None


def test_extraction_request_cannot_be_read_as_campaign_preparation(stored):
    stored.journal.register(stored.principal, stored.snapshot)
    with pytest.raises(ValueError, match='preparation_purpose'):
        CampaignPreparationJournal(stored.engine).read(stored.principal, stored.snapshot.document().reference)


def test_unissued_reservation_allows_preparation_and_exact_replay_after_issue_is_not_new_issuance(campaign_store):
    s = campaign_store
    s.requests.register(s.principal, s.plan.request)
    ledger = BudgetLedger(s.engine)
    reserved = ledger.reserve(s.principal, s.binding, policy(s.plan.request))
    original = s.journal.register(s.principal, s.plan, s.packet)
    dispatch = DispatchJournal(s.engine)
    assert dispatch.issue(s.principal, s.binding, 30) is not None
    assert s.journal.register(s.principal, s.plan, s.packet) == original
    assert dispatch.issue(s.principal, s.binding, 30) is None
    assert ledger.read(s.principal, s.binding.reference()) == reserved


@pytest.mark.parametrize('effect', ['dispatch', 'observation'])
def test_first_preparation_after_call_or_observation_is_rejected(campaign_store, effect):
    s = campaign_store
    s.requests.register(s.principal, s.plan.request)
    if effect == 'dispatch':
        BudgetLedger(s.engine).reserve(s.principal, s.binding, policy(s.plan.request))
        assert DispatchJournal(s.engine).issue(s.principal, s.binding, 30) is not None
    else:
        s.requests.begin_attempt(s.principal, s.binding)
        s.requests.record(s.principal, s.binding, observe(s.binding, FixtureProvider('interrupted')))
    with pytest.raises(ValueError, match='preparation_after_call'):
        s.journal.register(s.principal, s.plan, s.packet)
    assert s.journal.read(s.principal, s.plan.request.document().reference) is None


@pytest.mark.parametrize('field', ['tenant_id', 'project_id', 'engagement_id', 'request_sha256', 'manifest_sha256', 'plan_sha256', 'packet_sha256'])
def test_duplicate_sql_identity_corruption_is_detected_without_modifying_history(campaign_store, field):
    s = campaign_store
    original = registered(s)
    key = s.requests._key(s.plan.request.document().reference)
    with s.engine.connect() as connection:
        row = dict(connection.execute(text('SELECT * FROM planning.campaign_preparations WHERE ' + KEY), key).mappings().one())
    row[field] = '0' * 64 if field.endswith('sha256') else 'foreign'
    with pytest.raises(ValueError, match='stored_campaign_preparation_corrupt'):
        s.journal._stored(row, key, s.plan.request)
    assert s.journal.read(s.principal, s.plan.request.document().reference) == original


def test_failure_after_insert_rolls_back_the_whole_preparation(campaign_store, monkeypatch):
    s = campaign_store
    s.requests.register(s.principal, s.plan.request)
    read = s.journal._read

    def fail_after_insert(connection, key, request):
        result = read(connection, key, request)
        if result is not None:
            raise RuntimeError('injected rollback oracle')
        return result

    monkeypatch.setattr(s.journal, '_read', fail_after_insert)
    with pytest.raises(RuntimeError, match='rollback oracle'):
        s.journal.register(s.principal, s.plan, s.packet)
    monkeypatch.setattr(s.journal, '_read', read)
    assert s.journal.read(s.principal, s.plan.request.document().reference) is None
    assert registered(s).record.packet.canonical == s.packet.canonical


def test_service_cannot_update_or_delete_even_an_empty_match(campaign_store):
    for statement in ('DELETE FROM planning.campaign_preparations WHERE false',
                      'UPDATE planning.campaign_preparations SET tenant_id=tenant_id WHERE false'):
        with pytest.raises(DBAPIError), campaign_store.engine.begin() as connection:
            connection.execute(text(statement))


@pytest.mark.parametrize('different', [False, True], ids=['same-packet', 'different-packets'])
def test_competing_preparations_commit_one_immutable_result(campaign_store, different):
    s = campaign_store
    s.requests.register(s.principal, s.plan.request)
    options = [(s.plan, s.packet), alternative(s) if different else (s.plan, s.packet)]
    gate = Barrier(2)

    def write(option):
        gate.wait(timeout=5)
        try:
            return s.journal.register(s.principal, *option)
        except ValueError as error:
            assert str(error) == 'campaign_preparation_conflict'
            return None

    with ThreadPoolExecutor(2) as workers:
        results = list(workers.map(write, options))
    committed = s.journal.read(s.principal, s.plan.request.document().reference)
    successes = [row for row in results if row is not None]
    assert len(successes) == (1 if different else 2)
    assert all(row == committed for row in successes)


def test_registration_racing_dispatch_has_no_late_first_insert(campaign_store):
    s = campaign_store
    s.requests.register(s.principal, s.plan.request)
    BudgetLedger(s.engine).reserve(s.principal, s.binding, policy(s.plan.request))
    gate = Barrier(2)

    def register():
        gate.wait(timeout=5)
        try:
            return s.journal.register(s.principal, s.plan, s.packet)
        except ValueError as error:
            assert str(error) == 'campaign_preparation_after_call'
            return None

    def issue():
        gate.wait(timeout=5)
        return DispatchJournal(s.engine).issue(s.principal, s.binding, 30)

    with ThreadPoolExecutor(2) as workers:
        registration, dispatch = workers.submit(register), workers.submit(issue)
        prepared, issued = registration.result(timeout=15), dispatch.result(timeout=15)
    assert issued is not None
    assert s.journal.read(s.principal, s.plan.request.document().reference) == prepared
    if prepared is None:
        with pytest.raises(ValueError, match='preparation_after_call'):
            s.journal.register(s.principal, s.plan, s.packet)
    else:
        assert s.journal.register(s.principal, s.plan, s.packet) == prepared
