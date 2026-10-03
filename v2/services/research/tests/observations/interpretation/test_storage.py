"""Actual PostgreSQL atomicity, exact owner history and future-only correction behavior."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from amphora_contracts_research import (
    AssessObservationUseRequest,
    NormalizationTargetRecord,
    NormalizeObservationRequest,
    ObservationQuality,
)
from amphora_research.experiments.store import ExperimentStore
from amphora_research.observations.identity import ObservationError
from amphora_research.observations.interpretation.intent import InterpretationIntent
from amphora_research.observations.interpretation.profiles import InterpretationProfile
from amphora_research.observations.interpretation.store import InterpretationStore
from amphora_research.observations.records import ReportedQuality
from amphora_research.observations.store import ObservationStore
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError

from ...material_state.storage_fixtures import publish_specimen
from ..normalization.test_catalog import catalog
from ..quality.test_policy import policy

pytestmark = pytest.mark.postgres
TABLES = ("interpretation_intents","interpretation_results","interpretation_sources",
    "interpretation_observations","interpretation_material_states","interpretation_experiments")


def prepared_case(ledger,use=True):
    identities,scope = ledger
    _,plan,row = publish_specimen(identities,scope)
    ExperimentStore(identities.engine).publish(scope,"fixture",plan)
    ObservationStore(identities.engine).publish(scope,"fixture",row)
    profile = InterpretationProfile(scope,policy() if use else catalog())
    base = dict(wire_version="1",kind=profile.kind,interpretation_id="interpretation-1",profile=profile.reference)
    request = (AssessObservationUseRequest(**base,experiment=plan.reference,observations=(row.reference,)) if use else
        NormalizeObservationRequest(**base,observation=row.reference,targets=NormalizationTargetRecord(value_unit="g",coordinate_unit=None)))
    store = InterpretationStore(identities.engine)
    return store,profile,request


@pytest.mark.parametrize("use",[False,True])
def test_concurrent_completion_replacement_and_offline_original_actor_replay(ledger,use):
    store,profile,request = prepared_case(ledger,use)
    accepted = store.begin(profile,request,"actor")
    assert accepted.status == "pending"
    prepared = store.prepare(accepted.intent)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _:store.complete(prepared,prepared.sources),range(2)))
    assert results[0] == results[1] and results[0].status == "interpreted"
    replacement = InterpretationStore(store.engine)
    assert replacement.read(profile.scope,"actor",profile.kind,request.interpretation_id) == results[0]
    assert replacement.begin(profile,request,"actor") == results[0]
    assert set(results[0].result.sources) == set(prepared.sources)
    assert len(prepared.sources) == (4 if use else 1)
    assert InterpretationIntent.restore(accepted.intent.content) == accepted.intent
    with pytest.raises(ObservationError,match="actor_mismatch"):
        replacement.read(profile.scope,"other",profile.kind,request.interpretation_id)
    assert replacement.read(profile.scope.model_copy(update={"project_id":"absent"}),"actor",profile.kind,request.interpretation_id) is None
    with store.engine.connect() as connection:
        for table in TABLES:
            count = connection.execute(text(f"SELECT count(*) FROM research.{table} WHERE tenant_id=:tenant AND project_id=:project"),accepted.intent.key).scalar_one()
            assert count == (len(prepared.sources) if table == "interpretation_sources" else
                0 if not use and table in ("interpretation_material_states","interpretation_experiments") else 1)


@pytest.mark.parametrize("table",["interpretation_results","interpretation_sources","interpretation_observations",
    "interpretation_material_states","interpretation_experiments"])
def test_failure_at_each_result_or_dependency_write_rolls_back_whole_result(ledger,table):
    store,profile,request = prepared_case(ledger)
    accepted = store.begin(profile,request,"actor")
    prepared = store.prepare(accepted.intent)
    def fail(connection,cursor,statement,parameters,context,many):
        if statement.startswith("INSERT INTO research."+table):
            raise RuntimeError("injected index failure")
    event.listen(store.engine,"before_cursor_execute",fail)
    try:
        with pytest.raises(RuntimeError,match="injected"):
            store.complete(prepared,prepared.sources)
    finally:
        event.remove(store.engine,"before_cursor_execute",fail)
    assert store.read(profile.scope,"actor",profile.kind,request.interpretation_id).status == "pending"
    with store.engine.connect() as connection:
        for target in TABLES[1:]:
            assert connection.execute(text(f"SELECT count(*) FROM research.{target} WHERE tenant_id=:tenant AND project_id=:project"),accepted.intent.key).scalar_one() == 0
    assert store.complete(prepared,prepared.sources).status == "interpreted"


def test_unknown_input_stays_pending_and_cannot_bypass_acceptance(ledger):
    store,profile,request = prepared_case(ledger,False)
    intent = InterpretationIntent.prepare(profile,request,"actor")
    with pytest.raises(ObservationError,match="not_started"):
        store.prepare(intent)
    request = request.model_copy(update={"observation":request.observation.model_copy(update={"observation_id":"absent"})})
    accepted = store.begin(profile,request,"actor")
    with pytest.raises(ObservationError,match="unknown_observation"):
        store.prepare(accepted.intent)
    assert store.read(profile.scope,"actor",profile.kind,request.interpretation_id).status == "pending"


def test_actor_configuration_and_requested_input_changes_conflict(ledger):
    store,profile,request = prepared_case(ledger)
    accepted = store.begin(profile,request,"actor")
    with pytest.raises(ObservationError,match="intent_conflict"):
        store.begin(profile,request,"other")
    changed = replace(profile,policy=policy(True))
    with pytest.raises(ObservationError,match="intent_conflict"):
        store.begin(changed,request.model_copy(update={"profile":changed.reference}),"actor")
    with pytest.raises(ObservationError,match="intent_conflict"):
        store.begin(profile,request.model_copy(update={"observations":()}),"actor")
    assert store.read(profile.scope,"actor",profile.kind,request.interpretation_id) == accepted


def test_source_omission_and_same_reference_forgery_cannot_create_result(ledger):
    store,profile,request = prepared_case(ledger)
    prepared = store.prepare(store.begin(profile,request,"actor").intent)
    with pytest.raises(ObservationError,match="dependency_missing"):
        store.complete(prepared,prepared.sources[:1])
    row = replace(prepared.observations[0],quality=ReportedQuality("passed",()))
    forged = replace(prepared,observations=(row,))
    with pytest.raises(ObservationError,match="owned_input_mismatch"):
        store.complete(forged,prepared.sources)
    assert store.read(profile.scope,"actor",profile.kind,request.interpretation_id).status == "pending"


def test_corrected_observation_is_next_interpretation_input_and_preserves_pending_pin(ledger):
    store,profile,request = prepared_case(ledger)
    accepted = store.begin(profile,request,"actor")
    prepared = store.prepare(accepted.intent)
    observations = ObservationStore(store.engine)
    old = observations.read(profile.scope,request.observations[0])
    corrected = old.model_copy(update={"reference":old.reference.model_copy(update={"revision":2}),"supersedes":old.reference,
        "quality":ObservationQuality(controls="failed",flags=("low_accuracy",))})
    observations.publish(profile.scope,"fixture-correction",corrected)
    original_result = store.complete(prepared,prepared.sources)
    assert original_result.result.reviews[0].observation == old
    successor = request.model_copy(update={"interpretation_id":"next-iteration","observations":(corrected.reference,)})
    next_input = store.prepare(store.begin(profile,successor,"actor").intent)
    later = store.complete(next_input,next_input.sources).result
    assert later.reviews[0].observation == corrected and later.reviews[0].disposition == "usable"
    assert "controls_failed" in later.reviews[0].focus
    assert store.read(profile.scope,"actor",profile.kind,request.interpretation_id) == original_result


def test_complete_dependency_preparation_includes_material_processing_and_feature_sources(ledger):
    from amphora_research.material_state import wire as material_wire
    from amphora_research.material_state.preparation import PreparationHistory
    from amphora_research.material_state.store import MaterialStateStore

    from ...experiments.fixtures import experiment
    from ...material_state.storage_fixtures import in_scope, publish_candidate, records
    from ...material_state.test_context import event as processing_event
    from ...material_state.test_context import feature

    identities,scope = ledger
    state,plan,row = records(scope)
    richer = replace(experiment().samples[0].state,preparation=PreparationHistory((processing_event(),)),features=(feature(),))
    state = in_scope(material_wire.to_wire(richer),scope)
    plan = plan.model_copy(update={"samples":(plan.samples[0].model_copy(update={"state":state}),)})
    publish_candidate(identities,state)
    MaterialStateStore(identities.engine).publish(scope,"fixture",state)
    identities.publish(scope,plan.samples[0].sample)
    ExperimentStore(identities.engine).publish(scope,"fixture",plan)
    ObservationStore(identities.engine).publish(scope,"fixture",row)
    profile = InterpretationProfile(scope,policy())
    request = AssessObservationUseRequest(wire_version="1",kind=profile.kind,interpretation_id="rich-context",
        profile=profile.reference,experiment=plan.reference,observations=(row.reference,))
    store = InterpretationStore(identities.engine)
    prepared = store.prepare(store.begin(profile,request,"actor").intent)
    assert state.preparation[0].attribution.source in prepared.sources
    assert state.features[0].evidence.source in prepared.sources
    assert prepared.material_states == (state.reference,)
    assert set(store.complete(prepared,prepared.sources).result.sources) == set(prepared.sources)


def test_lost_reply_retries_exact_result_and_changed_output_cannot_overwrite(ledger):
    store,profile,request = prepared_case(ledger)
    prepared = store.prepare(store.begin(profile,request,"actor").intent)
    committed = store.complete(prepared,prepared.sources)
    # A dropped reply cannot change the accepted configuration or committed result.
    assert store.begin(profile,request,"actor") == committed
    assert store.complete(prepared,prepared.sources) == committed
    row = replace(prepared.observations[0],quality=ReportedQuality("passed",()))
    with pytest.raises(ObservationError,match="result_conflict"):
        store.complete(replace(prepared,observations=(row,)),prepared.sources)
    assert store.read(profile.scope,"actor",profile.kind,request.interpretation_id) == committed


def test_unknown_material_context_is_not_an_owned_material_dependency(ledger):
    store,profile,request = prepared_case(ledger)
    experiments = ExperimentStore(store.engine)
    old = experiments.read(profile.scope,request.experiment)
    unknown = old.model_copy(update={"reference":old.reference.model_copy(update={"revision":2}),"supersedes":old.reference,
        "samples":(old.samples[0].model_copy(update={"state":None}),)})
    experiments.publish(profile.scope,"fixture",unknown)
    request = request.model_copy(update={"experiment":unknown.reference,"observations":()})
    prepared = store.prepare(store.begin(profile,request,"actor").intent)
    assert prepared.material_states == ()
    result = store.complete(prepared,prepared.sources).result
    assert result.experiment.samples[0].state is None and result.missing_expectations == ("readout",)


@pytest.mark.parametrize("table",TABLES)
def test_service_cannot_update_or_delete_interpretation_history(ledger,table):
    store,profile,request = prepared_case(ledger)
    prepared = store.prepare(store.begin(profile,request,"actor").intent)
    store.complete(prepared,prepared.sources)
    for statement in (f"DELETE FROM research.{table}",f"UPDATE research.{table} SET interpretation_id='changed'"):
        with pytest.raises(DBAPIError):
            with store.engine.begin() as connection:
                connection.execute(text(statement+" WHERE tenant_id=:tenant AND project_id=:project"),prepared.intent.key)
