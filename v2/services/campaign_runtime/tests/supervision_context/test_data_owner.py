"""Actual public Data process validates and serves every prepared context Artifact."""

import hashlib
import json
import secrets
import sys
from dataclasses import replace
from pathlib import Path
from urllib.request import ProxyHandler, Request, build_opener

from amphora_campaign_runtime.artifact_bindings.publication import ArtifactPublisher
from amphora_campaign_runtime.compiler.catalog import canonical
from amphora_campaign_runtime.supervision_context.preparation import ContextPreparer
from amphora_campaign_runtime.supervision_policy import ReviewedPolicy
from amphora_campaign_runtime.supervision_policy.records import RecipePolicyRecord
from amphora_campaign_runtime.supervision_preparation.catalog import RecipeCatalog
from amphora_contracts_supervision import (
    SupervisionRef,
    checkpoint_context_content_schema,
    checkpoint_context_content_schema_bytes,
)
from campaign_context_fixture.data import command
from campaign_context_fixture.support import Owner, environment
from postgres_fixture import owned_state
from sqlalchemy import URL

from ..supervision_checkpoints.test_coordinator import slots
from ..supervision_policy.test_admission import command as admit_command
from ..supervision_preparation.test_policy_pins import configuration, service
from ..supervision_preparation.test_recipe import bind


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    return path


def publish_text(owner, scope, key, raw, schema):
    content = {'sha256': hashlib.sha256(raw).hexdigest(), 'size_bytes': len(raw), 'media_type': 'text/plain', 'schema_ref': schema}
    upload = owner.call('POST', '/v1/uploads', command(scope, 'artifacts.begin_upload', key + '.begin', {'content': content}))
    owner.call('PUT', '/v1/uploads/' + upload['upload_id'] + '/content', raw)
    return owner.call('POST', '/v1/artifacts/finalize', command(scope, 'artifacts.finalize', key + '.finalize',
        {'upload_id': upload['upload_id'], 'content': content}))['artifact']


def test_actual_data_context_publication_processing_reads_and_replacement(graph_env, tmp_path):
    graph = graph_env
    actor = replace(graph.env.principal, actions=graph.env.principal.actions | {'supervise_prepare'})
    graph.env.principal = actor
    scope = actor.scope.model_dump(mode='json')
    recipe, policy = configuration(graph)
    raw_policy_schema = canonical(RecipePolicyRecord.model_json_schema(mode='validation'))
    (tmp_path / 'policy-schema.json').write_bytes(raw_policy_schema)
    (tmp_path / 'context-schema.json').write_bytes(checkpoint_context_content_schema_bytes())
    text_schema = {'schema_id': 'fixture.context-text', 'version': '1', 'sha256': hashlib.sha256(b'{"type":"string"}').hexdigest()}
    profiles = [dict(text_schema, media_type='text/plain'),
        {'schema_id': 'runtime.supervision-policy.v2', 'version': '1', 'sha256': hashlib.sha256(raw_policy_schema).hexdigest(),
         'media_type': 'application/json', 'schema_path': 'policy-schema.json'},
        dict(checkpoint_context_content_schema().model_dump(mode='json'), media_type='application/json', schema_path='context-schema.json')]
    storage = tmp_path / 'bytes'
    storage.mkdir()
    config = write(tmp_path / 'data.json', {'database_url_env': 'CONTEXT_DATA_SQL', 'storage_root': str(storage),
        'profiles': profiles, 'limits': {'max_bytes': 1048576, 'scope_bytes': 8388608},
        'principals': [{'token_env': 'CONTEXT_DATA_TOKEN', 'actor_id': 'fixture', 'scope': scope,
                        'actions': ['upload', 'finalize', 'read']}]})
    state = owned_state()
    host, port = state['endpoint'].split(':')
    url = URL.create('postgresql+psycopg', username='artifact_service', password=state['password'], host=host,
                     port=int(port), database=state['database']).render_as_string(hide_password=False)
    token = secrets.token_hex(32)
    env = dict(environment(), CONTEXT_DATA_SQL=url, CONTEXT_DATA_TOKEN=token)
    owner = Owner(Path(sys.executable).absolute(), 'amphora_data_artifacts', config, env, token, tmp_path)
    pids = [owner.process.pid]
    try:
        data = recipe.document().model_dump(mode='json')
        prompt = (Path(__file__).parent / 'fixtures/campaign-v1.txt').read_bytes().replace(b'\r\n', b'\n')
        for key, raw in [('objective', b'Synthetic checkpoint objective'), ('prompt', prompt),
                         ('budget_policy', b'Synthetic policy reference; paid-call validation is a later gate')]:
            data[key] = publish_text(owner, scope, key, raw, text_schema)
        data['model']['configuration'] = publish_text(owner, scope, 'configuration', b'Synthetic deterministic model configuration', text_schema)
        data['entries'][0]['artifact'] = publish_text(owner, scope, 'source', b'Synthetic context only; scientific authority not established', text_schema)
        data['omissions'] = []
        recipe = bind(data)
        record = policy.document().model_dump(mode='json')
        record['context_recipe_sha256'] = recipe.sha256
        record['checkpoints'][0]['timeout_seconds'] = 300
        policy = ReviewedPolicy.bind(policy.plan, RecipePolicyRecord.model_validate_json(json.dumps(record)))
        receipt = service(graph, policy, RecipeCatalog([recipe])).admit_supervised(actor, admit_command(graph, policy))
        run = receipt.outcome.committed.object_id
        slot = slots(graph, run, policy)[0]
        reference = SupervisionRef(scope=actor.scope, run_id=run, decision_id=slot.seed.decision_id)
        actors = {(actor.scope.tenant_id, actor.scope.project_id, actor.actor_id): 'fixture'}
        original = ContextPreparer(graph.env.engine, actors, ArtifactPublisher(owner.endpoint, token, 'fixture')).prepare(actor, reference)
        context = original.frame.request.planning_request.context
        references = (context.objective, context.prompt, context.policy, context.model.configuration,
                      recipe.document().budget_policy, *(entry.artifact for entry in context.entries))
        for ref in references:
            request = Request(owner.endpoint + '/v1/artifacts/' + ref.artifact_id + '/processing-content',
                              headers={'Authorization': 'Bearer ' + token})
            with build_opener(ProxyHandler({})).open(request, timeout=10) as response:
                raw = response.read(1048577)
            assert len(raw) == ref.size_bytes and hashlib.sha256(raw).hexdigest() == ref.sha256
        owner.close()
        assert owner.process.poll() is not None
        owner = Owner(Path(sys.executable).absolute(), 'amphora_data_artifacts', config, env, token, tmp_path)
        pids.append(owner.process.pid)
        replayed = ContextPreparer(graph.env.engine, actors, ArtifactPublisher(owner.endpoint, token, 'fixture')).prepare(actor, reference)
        assert replayed == original
        write(tmp_path / 'evidence.json', {'run_id': run, 'decision_id': reference.decision_id,
            'request_sha256': original.frame.request_sha256, 'processing_reads': len(references), 'data_pids': pids,
            'limitation': 'Data publication/read proof; no Planning packet or paid-call validation'})
    finally:
        owner.close()
        assert owner.process.poll() is not None
