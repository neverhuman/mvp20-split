"""Actual owner transactions preserve all-or-none report batches and immutable retries."""
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from amphora_contracts_research import LabIntakeRequest, LabReturnProfile
from amphora_research.observations.identity import ObservationError
from amphora_research.observations.intake import IntakeIntent
from amphora_research.observations.intake_store import LabIntakeStore
from amphora_research.observations.reports import ConfiguredLabReturn
from amphora_research.observations.wire import from_wire, to_wire
from amphora_research.persistence.revisions import ScientificStoreError
from sqlalchemy import text

from .test_intake import intake_case

pytestmark = pytest.mark.postgres


def stored_case(ledger):
    identities,scope = ledger
    intent,resolved = intake_case()
    old = scope.model_dump(mode="json")
    def rescope(value):
        if isinstance(value,dict):
            if set(value) == {"tenant_id","project_id"}:
                return old
            return {key:rescope(item) for key,item in value.items()}
        if isinstance(value,list):
            return [rescope(item) for item in value]
        return value
    def copy(model):
        return type(model).model_validate_json(json.dumps(rescope(model.model_dump(mode="json"))))
    configured = ConfiguredLabReturn(LabReturnProfile.model_validate_json(json.dumps(rescope(intent.configured.document.model_dump(mode="json")))))
    source = copy(intent.request.report)
    request = LabIntakeRequest(wire_version="1",intake_id="intake",profile=configured.reference,report=source)
    intent = IntakeIntent.bind(configured,request,"fixture",scope)
    report = replace(resolved.report,configured=configured,source=source,raw_report=copy(resolved.report.raw_report),
        context_sources=tuple(copy(item) for item in resolved.report.context_sources),
        entries=tuple(replace(item,observation=from_wire(copy(to_wire(item.observation)))) for item in resolved.report.entries))
    return LabIntakeStore(identities.engine),intent,replace(resolved,report=report,inputs=tuple(copy(item) for item in resolved.inputs))


def test_pending_then_partial_outcome_survives_store_replacement(ledger):
    store,intent,resolved = stored_case(ledger)
    assert store.begin(intent).status.outcome.status == "pending"
    result = store.complete(intent,resolved)
    replacement = LabIntakeStore(store.engine)
    assert replacement.read(intent.request.profile.scope,"fixture","intake") == result
    assert replacement.complete(intent,resolved) == result
    assert replacement.begin(intent) == result
    assert result.status.outcome.resolution.disposition == "partial"
    observation = result.status.outcome.resolution.observations[0]
    assert replacement.observations.read(intent.request.profile.scope,observation.reference) == observation


def test_batch_conflict_rolls_back_earlier_observation_and_terminal(ledger):
    store,intent,resolved = stored_case(ledger)
    entry = resolved.report.entries[0]
    first = to_wire(entry.observation)
    first = first.model_copy(update={"reference":first.reference.model_copy(update={"observation_id":"a-first"})})
    last = first.model_copy(update={"reference":first.reference.model_copy(update={"observation_id":"z-conflict"})})
    conflict = last.model_copy(update={"source":resolved.report.raw_report})
    store.observations.publish(intent.request.profile.scope,"fixture",conflict)
    resolved = replace(resolved,report=replace(resolved.report,entries=(
        replace(entry,observation=from_wire(first)),replace(entry,observation=from_wire(last)))))
    store.begin(intent)
    with pytest.raises(ScientificStoreError,match="immutable_scientific_revision_conflict"):
        store.complete(intent,resolved)
    assert store.observations.read(intent.request.profile.scope,first.reference) is None
    assert store.read(intent.request.profile.scope,"fixture","intake").terminal is None
    assert store.observations.read(intent.request.profile.scope,last.reference) == conflict


def test_concurrent_identical_completions_and_original_actor(ledger):
    store,intent,resolved = stored_case(ledger)
    store.begin(intent)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _:store.complete(intent,resolved),range(2)))
    assert results[0] == results[1]
    other = IntakeIntent.bind(intent.configured,intent.request,"other",intent.request.profile.scope)
    with pytest.raises(ObservationError,match="lab_intake_identity_conflict"):
        store.begin(other)
    with pytest.raises(ObservationError,match="lab_intake_actor_mismatch"):
        store.read(intent.request.profile.scope,"other","intake")


def test_first_terminal_is_immutable_and_explicit_failure_is_not_science(ledger):
    store,intent,resolved = stored_case(ledger)
    with pytest.raises(ObservationError,match="lab_intake_not_started"):
        store.complete(intent,resolved)
    store.begin(intent)
    failed = store.fail(intent,"malformed_report")
    assert failed == store.fail(intent,"malformed_report")
    with pytest.raises(ObservationError,match="lab_intake_terminal_conflict"):
        store.complete(intent,resolved)
    assert store.read(intent.request.profile.scope,"fixture","intake") == failed


def test_tables_are_append_only_and_links_match_committed_observations(ledger):
    store,intent,resolved = stored_case(ledger)
    store.begin(intent)
    store.complete(intent,resolved)
    with store.engine.connect() as connection:
        count = connection.execute(text("SELECT count(*) FROM research.lab_observations WHERE tenant_id=:tenant AND project_id=:project AND intake_id=:id"),intent.key).scalar_one()
        assert count == 1
        for table in ("lab_intents","lab_terminals","lab_observations"):
            for privilege in ("UPDATE","DELETE","TRUNCATE","REFERENCES","TRIGGER"):
                assert not connection.execute(text("SELECT has_table_privilege(current_user,:table,:privilege)"),
                    {"table":f"research.{table}","privilege":privilege}).scalar_one()


def test_committed_terminal_with_lost_local_reply_recovers_without_new_rows(ledger):
    store,intent,resolved = stored_case(ledger)
    store.begin(intent)
    def reply_lost():
        store.complete(intent,resolved)
        raise ConnectionError("reply lost after commit")
    with pytest.raises(ConnectionError):
        reply_lost()
    replacement = LabIntakeStore(store.engine)
    before = replacement.read(intent.request.profile.scope,"fixture","intake")
    assert replacement.complete(intent,resolved) == before
    with store.engine.connect() as connection:
        for table in ("lab_terminals","lab_observations"):
            assert connection.execute(text(f"SELECT count(*) FROM research.{table} WHERE tenant_id=:tenant "
                "AND project_id=:project AND intake_id=:id"),intent.key).scalar_one() == 1


def test_changed_request_or_outcome_cannot_reuse_intake_identity(ledger):
    store,intent,resolved = stored_case(ledger)
    store.begin(intent)
    changed_request = intent.request.model_copy(update={"report":intent.request.report.model_copy(update={"artifact_id":"different"})})
    changed = IntakeIntent.bind(intent.configured,changed_request,"fixture",intent.request.profile.scope)
    with pytest.raises(ObservationError,match="lab_intake_identity_conflict"):
        store.begin(changed)
    expected = store.complete(intent,resolved)
    different = replace(resolved,report=replace(resolved.report,missing_expectations=()))
    with pytest.raises(ObservationError,match="lab_intake_terminal_conflict"):
        store.complete(intent,different)
    assert store.read(intent.request.profile.scope,"fixture","intake") == expected


def test_read_is_scoped_and_outage_leaves_intent_pending(ledger):
    store,intent,_ = stored_case(ledger)
    store.begin(intent)
    # No terminal is manufactured when resolution has not succeeded.
    replacement = LabIntakeStore(store.engine)
    scope = intent.request.profile.scope
    assert replacement.read(scope,"fixture","intake").status.outcome.status == "pending"
    assert replacement.read(scope.model_copy(update={"project_id":"other"}),"fixture","intake") is None
    assert replacement.read(scope,"fixture","unknown") is None
