"""Scripted authentication boundaries over actual owner persistence; independent HTTP is a later tier."""
import pytest
from amphora_research.assessment.policy import AssessmentError
from amphora_research.assessment.reader import AssessmentPeerUnavailable
from amphora_research.interpretation_api.profiles import InterpretationProfiles
from amphora_research.interpretation_api.workflow import InterpretationWorkflow
from amphora_research.observations.identity import ObservationError

from ..observations.interpretation.test_storage import prepared_case

pytestmark = pytest.mark.postgres


class Reader:
    def __init__(self, scope, sources, error=None):
        self.scope,self.sources,self.error = scope,sources,error
        self.seen = []

    @property
    def consumed(self):
        return tuple(self.seen)

    def read(self, reference):
        if self.error is not None:
            raise self.error
        assert reference in self.sources
        self.seen.append(reference)
        return b"fixture; only the reader contract is scripted"


def unavailable(scope):
    raise AssessmentPeerUnavailable("fixture_offline")


@pytest.mark.parametrize("use",[False,True])
def test_pending_retry_pins_config_and_completed_history_is_offline(use,ledger):
    store,profile,request = prepared_case(ledger,use)
    workflow = InterpretationWorkflow(store,InterpretationProfiles((profile,)),unavailable)
    with pytest.raises(AssessmentPeerUnavailable):
        workflow.submit(profile.scope,"actor",request)
    pending = workflow.read(profile.scope,"actor",profile.kind,request.interpretation_id)
    assert pending.outcome.status == "pending" and pending.request == request
    stored = store.read(profile.scope,"actor",profile.kind,request.interpretation_id)
    prepared = store.prepare(stored.intent)
    readers = []
    def fresh(scope):
        assert store.read(scope,"actor",profile.kind,request.interpretation_id).intent == stored.intent
        reader = Reader(scope,prepared.sources)
        readers.append(reader)
        return reader
    resumed = InterpretationWorkflow(store,InterpretationProfiles(),fresh)
    result = resumed.submit(profile.scope,"actor",request)
    assert result.outcome.status == "interpreted" and result.actor_id == "actor"
    assert set(readers[0].consumed) == set(prepared.sources)
    if not use:
        # Fixture mg/L has no declared conversion to g; that is a computed result.
        assert result.outcome.projection.result.status == "unresolved"
    offline = InterpretationWorkflow(store,InterpretationProfiles(),unavailable)
    assert offline.submit(profile.scope,"actor",request) == result
    assert offline.read(profile.scope,"actor",profile.kind,request.interpretation_id) == result
    assert offline.read(profile.scope,"actor",profile.kind,"absent") is None
    with pytest.raises(ObservationError,match="profile_unavailable"):
        offline.submit(profile.scope,"actor",request.model_copy(update={"interpretation_id":"new"}))


@pytest.mark.parametrize("error",[AssessmentError("peer_access_denied"),AssessmentError("reference_unavailable"),AssessmentPeerUnavailable("peer_unavailable")])
def test_source_failures_remain_pending_and_each_retry_uses_fresh_reader(ledger,error):
    store,profile,request = prepared_case(ledger)
    readers = []
    def fresh(scope):
        reader = Reader(scope,(),error)
        readers.append(reader)
        return reader
    workflow = InterpretationWorkflow(store,InterpretationProfiles((profile,)),fresh)
    for _ in range(2):
        with pytest.raises(type(error),match=str(error)):
            workflow.submit(profile.scope,"actor",request)
        assert workflow.read(profile.scope,"actor",profile.kind,request.interpretation_id).outcome.status == "pending"
    assert len(readers) == 2 and readers[0] is not readers[1]


def test_reader_reuse_or_wrong_scope_cannot_create_completed_projection(ledger):
    store,profile,request = prepared_case(ledger)
    accepted = store.begin(profile,request,"actor")
    prepared = store.prepare(accepted.intent)
    for reader in (Reader(profile.scope,prepared.sources),Reader(profile.scope.model_copy(update={"project_id":"other"}),())):
        if reader.scope == profile.scope:
            reader.read(prepared.sources[0])
        workflow = InterpretationWorkflow(store,InterpretationProfiles(),lambda _, selected=reader:selected)
        with pytest.raises(ObservationError,match="reader_scope_or_reuse"):
            workflow.submit(profile.scope,"actor",request)
    assert store.read(profile.scope,"actor",profile.kind,request.interpretation_id).status == "pending"


def test_completed_submit_cannot_retarget_inputs_actor_or_scope(ledger):
    store,profile,request = prepared_case(ledger)
    prepared = store.prepare(store.begin(profile,request,"actor").intent)
    store.complete(prepared,prepared.sources)
    workflow = InterpretationWorkflow(store,InterpretationProfiles(),unavailable)
    with pytest.raises(ObservationError,match="intent_conflict"):
        workflow.submit(profile.scope,"actor",request.model_copy(update={"observations":()}))
    with pytest.raises(ObservationError,match="actor_mismatch"):
        workflow.submit(profile.scope,"other",request)
    with pytest.raises(ObservationError,match="scope_mismatch"):
        workflow.submit(profile.scope.model_copy(update={"project_id":"other"}),"actor",request)


def test_active_profile_registry_rejects_ambiguous_or_unbounded_configuration(ledger):
    _,profile,_ = prepared_case(ledger)
    for profiles,reason in (((profile,profile),"duplicate"),((profile,)*33,"limit"),((object(),),"required")):
        with pytest.raises(ObservationError,match=reason):
            InterpretationProfiles(profiles)
