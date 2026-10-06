from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from amphora_contracts_fitness import FitnessSelection
from amphora_research.assessment.policy import AssessmentError
from amphora_research.fitness.operations import FitnessOperations
from amphora_research.fitness.policy import FitnessError
from amphora_research.fitness.store import FitnessStore
from amphora_research.transport.access import AccessDenied
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError

from .storage_fixtures import stored_case

pytestmark = pytest.mark.postgres


def selection(request):
    return FitnessSelection(scope=request.profile.scope,fitness_id=request.fitness_id)


def test_concurrent_replay_replacement_and_current_denial_keep_original_history(ledger):
    operations,principal,request,reader = stored_case(ledger)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first,second = pool.map(lambda _:operations.assemble(principal,request),range(2))
    assert first == second and first.disposition == 'ready'
    assert first.reuse_authority == 'none' and first.identity.authority == 'identity_only'
    assert first.axes[0].value.value == '1.25'
    replacement = FitnessOperations(ledger[0],tuple(operations.profiles.values()),lambda scope:reader)
    assert replacement.assemble(principal,request) == first
    calls = len(reader.calls)
    reader.error = AssessmentError('peer_access_denied')
    with pytest.raises(AssessmentError,match='peer_access_denied'):
        replacement.assemble(principal,request)
    assert len(reader.calls) > calls
    assert replacement.read(principal,selection(request)) == first
    with ledger[0].engine.connect() as connection:
        count = connection.execute(text('SELECT count(*) FROM research.fitness_projections WHERE project_id=:id'),{'id':principal.scope.project_id}).scalar_one()
    assert count == 1


def test_changed_identity_conflicts_and_scope_actor_and_action_are_separate(ledger):
    operations,principal,request,reader = stored_case(ledger)
    original = operations.assemble(principal,request)
    changed = request.model_copy(update={'declared_identity':request.declared_identity.model_copy(update={'artifact_id':'another-key'})})
    reader.source = changed.declared_identity
    with pytest.raises(FitnessError,match='identity_conflict'):
        operations.assemble(principal,changed)
    assert operations.read(principal,selection(request)) == original
    for denied in [replace(principal,actions=frozenset()),replace(principal,actor_id='other')]:
        with pytest.raises(AccessDenied):
            operations.read(denied,selection(request))
    with pytest.raises(AccessDenied):
        operations.read(principal,selection(request).model_copy(update={'scope':principal.scope.model_copy(update={'project_id':'other'})}))
    assert operations.read(principal,selection(request).model_copy(update={'fitness_id':'absent'})) is None


def test_failure_during_insert_rolls_back_then_retry_succeeds(ledger):
    operations,principal,request,_ = stored_case(ledger)
    def fail(connection,cursor,statement,parameters,context,many):
        if statement.startswith('INSERT INTO research.fitness_projections'):
            raise RuntimeError('injected_failure')
    event.listen(ledger[0].engine,'before_cursor_execute',fail)
    try:
        with pytest.raises(RuntimeError,match='injected_failure'):
            operations.assemble(principal,request)
    finally:
        event.remove(ledger[0].engine,'before_cursor_execute',fail)
    assert operations.read(principal,selection(request)) is None
    assert operations.assemble(principal,request).disposition == 'ready'


@pytest.mark.parametrize('statement', [
    'UPDATE research.fitness_projections SET actor_id=actor_id WHERE project_id=:id',
    'DELETE FROM research.fitness_projections WHERE project_id=:id',
])
def test_service_role_cannot_rewrite_or_delete_history(ledger,statement):
    operations,principal,request,_ = stored_case(ledger)
    original = operations.assemble(principal,request)
    with pytest.raises(DBAPIError), ledger[0].engine.begin() as connection:
        connection.execute(text(statement),{'id':principal.scope.project_id})
    assert operations.read(principal,selection(request)) == original


@pytest.mark.parametrize('change,error', [
    ('interpretation','reference_mismatch'),('owner_missing','record_unavailable'),
    ('foreign','scope_mismatch'),('schema','encoding_mismatch'),('bytes','bytes_mismatch'),
])
def test_invalid_dependencies_never_publish(ledger,change,error):
    operations,principal,request,reader = stored_case(ledger)
    if change == 'interpretation':
        request = request.model_copy(update={'interpretation':request.interpretation.model_copy(update={'sha256':'e'*64})})
    elif change == 'owner_missing':
        request = request.model_copy(update={'candidate':request.candidate.model_copy(update={'candidate_id':'missing'})})
    elif change == 'foreign':
        request = request.model_copy(update={'candidate':request.candidate.model_copy(update={'scope':principal.scope.model_copy(update={'project_id':'foreign'})})})
    elif change == 'schema':
        request = request.model_copy(update={'declared_identity':request.declared_identity.model_copy(update={'media_type':'text/plain'})})
    else:
        reader.raw = b'{}'
    with pytest.raises(FitnessError,match=error):
        operations.assemble(principal,request)
    assert operations.read(principal,selection(request)) is None
