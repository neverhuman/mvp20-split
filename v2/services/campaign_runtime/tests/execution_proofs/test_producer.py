import json
from dataclasses import replace

import pytest
from amphora_campaign_runtime.api import create_app
from amphora_campaign_runtime.completion.coordinator import CompletionCoordinator
from amphora_campaign_runtime.execution_proofs.projection import ProducerProofError, ProducerSnapshot
from amphora_campaign_runtime.execution_proofs.reads import ExecutionProofs
from amphora_campaign_runtime.inspection.cursors import InspectionError
from amphora_campaign_runtime.lifecycle.access import RuntimeCredentials
from amphora_campaign_runtime.lifecycle.authority import AuthorityCommands
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_contracts_execution_proofs import AcceptedToolExecution
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from ..inspection.test_history import Peer, history


def accepted(c):
    principal=replace(c.env.principal,actions=c.env.principal.actions|{'inspect_receipts'})
    command=c.command('runtime.complete',c.payload)
    result=CompletionCoordinator(c.env.engine,Peer()).complete(c.env.principal,command)
    assert result.outcome.status=='accepted'
    return principal,result.outcome.committed.object_id


def test_exact_accepted_inputs_outputs_and_worker_survive_replacement_and_revocation(completion_env):
    c=completion_env;principal,completion=accepted(c)
    proof=ExecutionProofs(c.env.engine).read(principal,c.run,completion)
    assert proof.invocation.tool==c.invocation.tool and proof.invocation.inputs==c.invocation.inputs
    assert proof.invocation.activation_id==c.invocation.activation_id
    assert proof.worker_id==c.env.principal.actor_id
    assert proof.completion.result.attempt_id==c.invocation.attempt_id
    assert proof.completion.result.fence==c.invocation.fence
    assert proof.completion.canonical_result and proof.completion.result.outcome.status=='succeeded'
    assert len(proof.completion.retention_reservation_ids)==1
    raw=proof.model_dump(mode='json')
    Draft202012Validator(AcceptedToolExecution.model_json_schema()).validate(raw)
    assert all(secret not in json.dumps(raw) for secret in ('grant_id','lease_expires_at','claim_command'))
    AuthorityCommands(c.env.engine).revoke(c.env.principal,c.command('runtime.revoke_worker',
        {'worker_id':c.env.principal.actor_id,'reason_code':'fixture_revocation'}))
    assert ExecutionProofs(c.env.engine).read(principal,c.run,completion)==proof


@pytest.mark.parametrize('retryable', [True, False], ids=['retryable', 'terminal'])
def test_pending_failed_and_other_scope_producers_are_unavailable(completion_env, retryable):
    c=completion_env
    principal=replace(c.env.principal,actions=c.env.principal.actions|{'inspect_receipts'})
    with pytest.raises(InspectionError,match='producer_unavailable'):
        ExecutionProofs(c.env.engine).read(principal,c.run,'pending')
    payload=dict(c.payload,completion=dict(c.payload['completion'],outcome={'status':'failed','reason_code':'synthetic_failure','retryable':retryable}))
    failed=CompletionCoordinator(c.env.engine,Peer()).complete(c.env.principal,c.command('runtime.complete',payload))
    assert failed.outcome.status=='accepted'
    with pytest.raises(InspectionError,match='producer_unavailable'):
        ExecutionProofs(c.env.engine).read(principal,c.run,failed.outcome.committed.object_id)


def test_each_grant_and_exact_scope_is_required(completion_env):
    c=completion_env;principal,completion=accepted(c)
    for action in ('read','inspect_receipts'):
        with pytest.raises(TransitionError,match='access_denied'):
            ExecutionProofs(c.env.engine).read(replace(principal,actions=principal.actions-{action}),c.run,completion)
    other=replace(principal,scope=principal.scope.model_copy(update={'project_id':'other'}))
    with pytest.raises(InspectionError,match='producer_unavailable'):
        ExecutionProofs(c.env.engine).read(other,c.run,completion)


@pytest.mark.parametrize('field,value',[('activation_id','foreign'),('invocation_id','foreign')])
def test_projection_cannot_bind_an_unrelated_invocation(completion_env,field,value):
    c=completion_env;principal,completion=accepted(c)
    proof=ExecutionProofs(c.env.engine).read(principal,c.run,completion)
    with pytest.raises(ProducerProofError,match='identity_inconsistent'):
        ProducerSnapshot(proof.invocation.model_copy(update={field:value}),proof.completion,proof.worker_id,c.invocation.attempt_id,c.invocation.fence)


def test_projection_checks_attempt_fence_and_nested_source_scope(completion_env):
    c=completion_env;principal,completion=accepted(c)
    proof=ExecutionProofs(c.env.engine).read(principal,c.run,completion)
    for attempt,fence in [('other',c.invocation.fence),(c.invocation.attempt_id,c.invocation.fence+1)]:
        with pytest.raises(ProducerProofError,match='identity_inconsistent'):
            ProducerSnapshot(proof.invocation,proof.completion,proof.worker_id,attempt,fence)
    source=proof.invocation.inputs[0]
    foreign=source.artifact.model_copy(update={'scope':source.artifact.scope.model_copy(update={'project_id':'foreign'})})
    changed=proof.invocation.model_copy(update={'inputs':(source.model_copy(update={'artifact':foreign}),)})
    with pytest.raises(ProducerProofError,match='source_scope_inconsistent'):
        ProducerSnapshot(changed,proof.completion,proof.worker_id,c.invocation.attempt_id,c.invocation.fence)


def test_public_endpoint_is_explicit_authorized_and_has_no_live_grant(completion_env):
    c=completion_env;principal,completion=accepted(c)
    credentials=RuntimeCredentials([('x'*32,principal),('r'*32,replace(principal,actions=frozenset({'read'})))])
    client=TestClient(create_app(c.env.service,credentials,history=history(c)))
    path=f'/v1/runs/{c.run}/completions/{completion}/producer'
    assert client.get(path).status_code==401
    assert client.get(path,headers={'Authorization':'Bearer '+'r'*32}).status_code==403
    response=client.get(path,headers={'Authorization':'Bearer '+'x'*32})
    assert response.status_code==200 and response.headers['cache-control']=='no-store'
    assert response.json()['authority']=='accepted_execution'
    assert '/v1/runs/{run_id}/completions/{completion_id}/producer' not in create_app().openapi()['paths']


def test_record_decode_failure_is_safe_service_unavailability(completion_env, monkeypatch):
    from amphora_campaign_runtime.execution_proofs import reads

    c = completion_env
    principal, completion = accepted(c)
    credentials = RuntimeCredentials([('x' * 32, principal)])
    client = TestClient(create_app(c.env.service, credentials, history=history(c)))

    class UndecodableInvocation:
        @staticmethod
        def model_validate_json(_value):
            raise ValueError('private stored record contents')

    # Exercise the real scoped SQL join with an injected decoding failure, without
    # modifying accepted immutable history to manufacture corrupt owner records.
    monkeypatch.setattr(reads, 'PreparedInvocation', UndecodableInvocation)
    response = client.get(f'/v1/runs/{c.run}/completions/{completion}/producer',
        headers={'Authorization': 'Bearer ' + 'x' * 32})
    assert response.status_code == 503
    assert response.json() == {'reason_code': 'producer_integrity_unavailable'}
    assert response.headers['cache-control'] == 'no-store'
