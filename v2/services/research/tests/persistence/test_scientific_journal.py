"""Real PostgreSQL grants, null-predecessor defense and committed-reply-loss reconciliation."""
from contextlib import contextmanager

import pytest
from amphora_contracts_research import (
    MeasurementInterval,
    MeasurementQuantity,
    NumericMeasurement,
    ObservationRevision,
    SeriesMeasurement,
    SeriesMeasurementPoint,
)
from amphora_research.observations.store import ObservationStore
from amphora_research.persistence.revisions import RevisionDocument, RevisionJournal, ScientificStoreError
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from ..material_state.storage_fixtures import records
from ..material_state.test_context import SCOPE

TABLES = ("material_state_revisions","experiment_revisions","observation_revisions",
          "material_state_candidates","sample_material_states","experiment_samples")


@pytest.mark.postgres
@pytest.mark.parametrize("table",TABLES)
def test_new_tables_grant_append_read_but_not_history_mutation(ledger,table):
    store,_ = ledger
    with store.engine.connect() as connection:
        for privilege in ("SELECT","INSERT"):
            assert connection.execute(text("SELECT has_table_privilege(current_user,:table,:privilege)"),
                                      {"table":"research."+table,"privilege":privilege}).scalar_one()
        for privilege in ("UPDATE","DELETE","TRUNCATE","REFERENCES","TRIGGER"):
            assert not connection.execute(text("SELECT has_table_privilege(current_user,:table,:privilege)"),
                                          {"table":"research."+table,"privilege":privilege}).scalar_one()
    for statement in (f"UPDATE research.{table} SET project_id=project_id WHERE FALSE",f"DELETE FROM research.{table} WHERE FALSE"):
        with pytest.raises(DBAPIError) as error, store.engine.begin() as connection:
            connection.execute(text(statement))
        assert error.value.orig.sqlstate == "42501"


@pytest.mark.postgres
@pytest.mark.parametrize("table",TABLES[:3])
def test_null_predecessor_cannot_bypass_database_revision_check(ledger,table):
    store,scope = ledger
    with pytest.raises(IntegrityError) as error, store.engine.begin() as connection:
        connection.execute(text(f"INSERT INTO research.{table} "
            "(tenant_id,project_id,identity_id,revision,prior_revision,actor_id,canonical_bytes) "
            "VALUES (:tenant,:project,'invalid',2,NULL,'fixture',:body)"),
            {"tenant":scope.tenant_id,"project":scope.project_id,"body":b"{}"})
    assert error.value.orig.sqlstate == "23514"


@pytest.mark.postgres
def test_actual_commit_then_lost_local_reply_replays_exact_history(ledger):
    identities,scope = ledger
    _,_,record = records(scope)
    class LostReply:
        @contextmanager
        def begin(self):
            with identities.engine.begin() as connection:
                yield connection
            raise RuntimeError("fixture_committed_reply_lost")
    with pytest.raises(RuntimeError,match="fixture_committed_reply_lost"):
        ObservationStore(LostReply()).publish(scope,"original-actor",record)
    replacement = ObservationStore(identities.engine)
    assert replacement.read(scope,record.reference) == record
    assert replacement.publish(scope,"retry-actor",record) == record
    with identities.engine.connect() as connection:
        actor,count = connection.execute(text("SELECT min(actor_id),count(*) FROM research.observation_revisions "
            "WHERE tenant_id=:tenant AND project_id=:project"),{"tenant":scope.tenant_id,"project":scope.project_id}).one()
        assert actor == "original-actor" and count == 1


@pytest.mark.parametrize("scope,actor,record,model,reason",[
    (SCOPE,"fixture",None,ObservationRevision,"scientific_record_type"),
    (SCOPE,"fixture",records(SCOPE)[2],str,"scientific_record_type"),
    (None,"fixture",records(SCOPE)[2],ObservationRevision,"scientific_record_scope_mismatch"),
    (SCOPE,"",records(SCOPE)[2],ObservationRevision,"scientific_record_shape"),
    (SCOPE,"fixture",records(SCOPE)[2].model_copy(update={"reference":None}),ObservationRevision,"scientific_record_shape"),
])
def test_invalid_private_records_fail_before_database_access(scope,actor,record,model,reason):
    with pytest.raises(ScientificStoreError,match=reason):
        RevisionDocument.prepare(scope,actor,record,model)


def test_private_table_selection_is_closed():
    with pytest.raises(ScientificStoreError,match="scientific_record_type"):
        RevisionJournal(None,str,None,None)


def test_large_valid_shape_is_rejected_without_truncating_source():
    q = MeasurementQuantity(value="1"*64,unit="mg/L")
    point = SeriesMeasurementPoint(x=MeasurementQuantity(value="1",unit="s"),
        y=NumericMeasurement(kind="numeric",quantity=q,uncertainty=MeasurementInterval(lower=q,upper=q,description="x"*512)))
    record = records(SCOPE)[2].model_copy(update={"value":SeriesMeasurement(kind="series",x_unit="s",y_unit="mg/L",points=(point,)*4096)})
    with pytest.raises(ScientificStoreError,match="scientific_record_limit"):
        RevisionDocument.prepare(SCOPE,"fixture",record,ObservationRevision)
    assert len(record.value.points) == 4096 and record.value.points[0].y.quantity.value == "1"*64
