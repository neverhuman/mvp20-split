from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from amphora_contracts_evaluation_reuse import ReuseSelection
from amphora_research.assessment.policy import AssessmentError
from amphora_research.evaluation_reuse.errors import ReuseError
from amphora_research.evaluation_reuse.operations import ReuseOperations
from amphora_research.transport.access import AccessDenied
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError

from .storage_fixtures import stored_case

pytestmark=pytest.mark.postgres


def selection(request):
    return ReuseSelection(scope=request.profile.scope,reuse_id=request.reuse_id)


def test_real_store_exact_retry_replacement_and_history_survive_current_denial(ledger):
    ops,principal,request,data,runtime=stored_case(ledger)
    first=ops.qualify(principal,request)
    assert first.status=='permitted' and first.reusable_artifact.artifact_id=='evaluation'
    replacement=ReuseOperations(ledger[0],tuple(ops.profiles.values()),lambda _:data,lambda _:runtime)
    assert replacement.qualify(principal,request)==first
    assert len(runtime.calls)==6
    data.error=AssessmentError('peer_access_denied')
    with pytest.raises(AssessmentError):replacement.qualify(principal,request)
    assert replacement.read(principal,selection(request))==first
    historical=ReuseOperations(ledger[0],(),lambda _:None,lambda _:None)
    assert historical.read(principal,selection(request))==first
    with pytest.raises(ReuseError,match='profile_unavailable'):historical.qualify(principal,request)
    with ledger[0].engine.connect() as connection:
        assert connection.execute(text('SELECT count(*) FROM research.evaluation_reuse WHERE project_id=:id'),{'id':principal.scope.project_id}).scalar_one()==1


def test_context_miss_is_durable_and_never_returns_an_artifact(ledger):
    ops,principal,request,_,_=stored_case(ledger,different_context=True)
    result=ops.qualify(principal,request)
    assert result.status=='miss' and result.reusable_artifact is None
    assert ops.read(principal,selection(request))==result


def test_scope_actor_action_conflict_and_append_only_rights(ledger):
    ops,principal,request,data,runtime=stored_case(ledger)
    original=ops.qualify(principal,request)
    alias=request.target.identity.model_copy(update={'artifact_id':'identity-alias'})
    data.contents['identity-alias']=data.contents[request.target.identity.artifact_id]
    changed=request.model_copy(update={'target':request.target.model_copy(update={'identity':alias})})
    with pytest.raises(ReuseError,match='reuse_identity_conflict'):ops.qualify(principal,changed)
    for denied in (replace(principal,actor_id='other'),replace(principal,actions=frozenset())):
        with pytest.raises(AccessDenied):ops.read(denied,selection(request))
    foreign=selection(request).model_copy(update={'scope':principal.scope.model_copy(update={'project_id':'foreign'})})
    with pytest.raises(AccessDenied):ops.read(principal,foreign)
    assert ops.read(principal,selection(request).model_copy(update={'reuse_id':'missing'})) is None
    for statement in ('UPDATE research.evaluation_reuse SET actor_id=actor_id WHERE project_id=:id',
                      'DELETE FROM research.evaluation_reuse WHERE project_id=:id'):
        with pytest.raises(DBAPIError),ledger[0].engine.begin() as connection:
            connection.execute(text(statement),{'id':principal.scope.project_id})
    assert ops.read(principal,selection(request))==original


def test_insert_rollback_and_concurrent_exact_retries(ledger):
    ops,principal,request,_,_=stored_case(ledger)
    def fail(connection,cursor,statement,parameters,context,many):
        if statement.startswith('INSERT INTO research.evaluation_reuse'):raise RuntimeError('injected_failure')
    event.listen(ledger[0].engine,'before_cursor_execute',fail)
    try:
        with pytest.raises(RuntimeError,match='injected_failure'):ops.qualify(principal,request)
    finally:event.remove(ledger[0].engine,'before_cursor_execute',fail)
    assert ops.read(principal,selection(request)) is None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:ops.qualify(principal,request),range(2)))
    assert results[0]==results[1]


def test_late_context_dependency_denial_prevents_publication(ledger,monkeypatch):
    ops,principal,request,data,_=stored_case(ledger)
    original=data.read
    def guarded(reference):
        if reference.artifact_id=='conditions':raise AssessmentError('peer_access_denied')
        return original(reference)
    monkeypatch.setattr(data,'read',guarded)
    with pytest.raises(AssessmentError,match='peer_access_denied'):ops.qualify(principal,request)
    assert ops.read(principal,selection(request)) is None
