"""Installed dynamic bindings via public owners and SDK workers; no private SQL."""

import hashlib
import importlib.util
import json
import sys
import tempfile
import threading
import time
from pathlib import Path


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ROOT = Path(__file__).absolute().parents[5]
GRAPH = load('binding_graph_helpers', ROOT / 'services/campaign_runtime/tests/scheduling/acceptance/probe.py')
DEFINITIONS = load('binding_definitions', Path(__file__).parents[1] / 'definitions.py')
RELAY = load('binding_artifact_relay', Path(__file__).with_name('relay.py'))
HTTP = GRAPH.HTTP


class BindingEnvironment(GRAPH.GraphEnvironment):
    def setup(self):
        self.scope['tenant_id'] = 'binding-acceptance'
        GRAPH.BASE.Environment.setup(self)
        artifact = json.loads(Path(self.artifact.config).read_bytes())
        next(p for p in artifact['principals'] if p['actor_id'] == 'runtime')['actions'].extend(['upload', 'finalize', 'read'])
        port = self.artifact.port
        self.artifact.close()
        self.artifact = self.host('artifact', 'amphora_data_artifacts', artifact, 'AMPHORA_ARTIFACT_DATABASE_URL', port)
        self.binding_relay = RELAY.ArtifactRelay(HTTP, self.artifact.endpoint)
        self.resources.append(self.binding_relay)
        entries = GRAPH.DEFINITIONS.configure(self)
        entry = entries[0]
        template = json.loads((self.root / entry['definition']).read_bytes())
        # The deliberate lease-expiry recovery pause must fit within the authored tool deadline.
        template['body']['nodes'][0]['timeout_seconds'] = self.tools[0].image['descriptor']['resources']['timeout_seconds']
        self.definition = DEFINITIONS.dynamic_graph(template)
        entry['definition'] = 'dynamic-binding.json'
        (self.root / entry['definition']).write_text(json.dumps(self.definition), encoding='utf-8')
        config = json.loads(Path(self.runtime.config).read_bytes())
        config.update(fixtures=[], graphs=[entry], bindings={'endpoint': self.binding_relay.endpoint, 'token_env': 'TOKEN_RUNTIME'})
        config['artifacts']['reserve_endpoint'] = self.binding_relay.endpoint + '/v1/reservations'
        next(p for p in config['principals'] if p['actor_id'] == 'admin')['actions'].append('maintain')
        port = self.runtime.port
        self.runtime.close()
        self.runtime = self.host('runtime', 'amphora_campaign_runtime', config, 'AMPHORA_RUNTIME_DATABASE_URL', port)
        self.plans = self.compile(self.config['runtime'])

    def graph(self):
        return HTTP.decoded(self.runtime.endpoint, '/v3/graph-runs/' + self.active_run, self.tokens['admin'])

    def proof(self, binding):
        return HTTP.decoded(self.runtime.endpoint, '/v1/completion-intents/outcome', self.tokens['artifact'], binding)

    def bytes(self, artifact):
        status, body = HTTP.request(self.artifact.endpoint, '/v1/artifacts/' + artifact['artifact_id'] + '/content', self.tokens['worker1'])
        assert status == 200 and len(body) == artifact['size_bytes'] and hashlib.sha256(body).hexdigest() == artifact['sha256']
        return body

    def report(self, worker, claim, publication):
        invocation = claim['outcome']['invocation']
        receipt = HTTP.decoded(self.runtime.endpoint, '/v1/commands/runtime.complete/complete-' + invocation['attempt_id'] +
            '?actor_id=' + worker.actor, self.tokens['admin'])
        completion = HTTP.decoded(self.runtime.endpoint, '/v1/runs/' + self.active_run + '/completions/' +
            receipt['outcome']['committed']['object_id'], self.tokens['admin'])
        artifact = completion['result']['outcome']['outputs'][0]['artifact']
        assert completion['canonical_result'] is True and len(completion['retention_reservation_ids']) == 1
        assert artifact == publication['artifact']
        source = json.loads(self.bytes(invocation['inputs'][0]['artifact']))
        result = json.loads(self.bytes(artifact))
        assert result['values'] == [value * source['a'] + source['b'] for value in source['values']]
        return {'invocation': invocation, 'receipt': receipt, 'completion': completion, 'result': result}


def interrupt_publication(e):
    before = e.graph()
    e.binding_relay.hold_finalize = True
    command = e.command('graph.advance', {'run_id': e.active_run})
    result = {}

    def request():
        try:
            result['reply'] = HTTP.request(e.runtime.endpoint, '/v1/graph-runs/advance', e.tokens['admin'], command)
        except Exception as error:
            result['transport_failure'] = type(error).__name__

    thread = threading.Thread(target=request, daemon=True)
    thread.start()
    assert e.binding_relay.reached.wait(20), 'Real Artifact finalization barrier was not reached'
    finalized = next(event for event in e.binding_relay.events if event.get('barrier'))
    reference = finalized['response']['artifact']
    content = e.bytes(reference)
    # Artifact committed, but Runtime has not received that response or accepted the binding.
    assert e.graph() == before
    e.replace_runtime()
    e.binding_relay.release.set()
    thread.join(20)
    assert not thread.is_alive()
    assert e.graph() == before
    deadline = time.monotonic() + 40
    while True:
        protected = [event['response']['outcome']['binding'] for event in e.binding_relay.events
            if event['path'] == '/v1/reservations' and event['status'] == 200 and
            event['response']['outcome']['binding']['artifact'] == reference]
        if protected and all(e.proof(binding)['proof']['status'] == 'committed' for binding in protected):
            break
        assert time.monotonic() < deadline, 'Original binding lease did not recover'
        e.advance()
        time.sleep(0.1)
    assert e.bytes(reference) == content
    history = HTTP.decoded(e.artifact.endpoint, '/v1/commands/artifacts.finalize/' + finalized['command']['identity']['command_id'], e.tokens['runtime'])
    assert history['outcome']['receipt'] == finalized['response']
    streams = [event for event in e.binding_relay.events if event['method'] == 'PUT' and
               event['path'] == '/v1/uploads/' + finalized['response']['upload_id'] + '/content']
    assert len(streams) == 1, 'Finalized replay must not stream again'
    e.record('BINDING-DEATH-AFTER-ARTIFACT-BEFORE-RUNTIME', {'before': before, 'after': e.graph(),
        'finalization': finalized['response'], 'history': history, 'stream_count': len(streams), 'transport': result.get('transport_failure')})


def scenarios(e):
    numeric = e.tools[0]
    seed = e.publish(numeric, {'values': [1, 2, 3], 'a': 1, 'b': 0})
    shape = e.definition['body']['inputs'][0]['value_type']
    command = e.command('graph.admit', {'plan_sha256': e.plans['binding-round-trip']['sha256'],
        'inputs': [{'port': 'parameters', 'value': {'kind': 'artifact', 'artifact': seed,
            'representation': shape['representation'], 'unit': shape['unit']}}], 'budget': {'limit': 20}})
    admission = HTTP.decoded(e.runtime.endpoint, '/v1/graph-runs', e.tokens['admin'], command)
    assert admission['outcome']['status'] == 'accepted'
    e.active_run = admission['outcome']['committed']['object_id']
    reports, interrupted, replaced = [], False, False
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        page = e.advance()
        if page['status'] != 'running':
            break
        pending = [node for node in page['nodes'] if node['kind'] == 'artifact_materialize' and node['status'] == 'issued']
        if pending and not interrupted:
            interrupt_publication(e)
            interrupted = True
            continue
        if interrupted and not replaced:
            before = e.graph()
            receipts = [event['response'] for event in e.binding_relay.events if event['path'] == '/v1/reservations' and event['status'] == 200]
            proofs = [e.proof(receipt['outcome']['binding']) for receipt in receipts]
            e.replace_runtime()
            assert e.graph() == before
            assert [e.proof(receipt['outcome']['binding']) for receipt in receipts] == proofs
            assert HTTP.decoded(e.runtime.endpoint, '/v1/graph-runs', e.tokens['admin'], command) == admission
            e.record('BINDING-REPLACEMENT-AFTER-COMMIT', {'graph': before, 'proofs': proofs, 'admission': admission})
            replaced = True
        if any(node['kind'] == 'invoke' and node['status'] == 'issued' for node in e.graph()['nodes']):
            reports.append(e.finish_worker(e.worker(numeric, 'worker1')))
        else:
            time.sleep(0.05)
    page = e.graph()
    assert page['status'] == 'completed' and page['spent'] == 10 and page['reserved'] == 0, {
        'status': page['status'], 'spent': page['spent'], 'reserved': page['reserved'],
        'unfinished': [(node['path'], node['status'], node['reason_code']) for node in page['nodes'] if node['status'] != 'succeeded']}
    assert interrupted and replaced and len(reports) == 10
    nodes = [node for node in page['nodes'] if node['kind'] in {'artifact_project', 'artifact_materialize'}]
    assert len(nodes) == 20 and all(node['status'] == 'succeeded' for node in nodes)
    publications = [event for event in e.binding_relay.events if event['path'] == '/v1/artifacts/finalize' and event['status'] == 200]
    final = publications[-1]['response']['artifact']
    assert json.loads(e.bytes(final)) == {'values': [7, 11, 15], 'a': 1, 'b': 0}
    receipts = {event['response']['outcome']['binding']['reservation_id']: event['response']
        for event in e.binding_relay.events if event['path'] == '/v1/reservations' and event['status'] == 200}
    proofs = {key: e.proof(receipt['outcome']['binding']) for key, receipt in receipts.items()}
    assert all(proof['proof']['status'] == 'committed' for proof in proofs.values())
    binding_proofs = [proof for proof in proofs.values() if proof['binding']['intent']['intent_id'].startswith('binding:')]
    assert len({proof['proof']['runtime_receipt_id'] for proof in binding_proofs}) == 20
    delivery = []
    for _ in range(8):
        delivery.append(e.owner_command('deliver', '--limit', '100', '--time-budget', '10'))
        retained = {key: HTTP.decoded(e.artifact.endpoint, '/v1/reservations/' + key, e.tokens['runtime']) for key in receipts}
        if all(receipt['outcome']['status'] == 'confirmed' for receipt in retained.values()):
            break
    assert all(receipt['outcome']['status'] == 'confirmed' for receipt in retained.values()), {
        'passes': delivery, 'unconfirmed': {key: value['outcome']['status'] for key, value in retained.items()
                                          if value['outcome']['status'] != 'confirmed'}}
    final_bytes = e.bytes(final)
    e.replace_runtime()
    assert e.graph() == page and e.bytes(final) == final_bytes
    assert {key: e.proof(receipt['outcome']['binding']) for key, receipt in receipts.items()} == proofs
    e.record('BINDING-INSTALLED-ROUND-TRIP', {'graph': page, 'seed': seed, 'final': final, 'final_values': [7, 11, 15],
        'reports': reports, 'proofs': proofs, 'retained': retained, 'delivery': delivery, 'plans': e.plans,
        'binding_requests': e.binding_relay.events, 'notification_target_configured': False})
    e.active_run = None


def main():
    config = json.loads(Path(sys.argv[1]).read_bytes())
    with tempfile.TemporaryDirectory(prefix='amphora-binding-peers-') as directory:
        e = BindingEnvironment(config, Path(directory))
        try:
            e.setup()
            scenarios(e)
            e.save('passed')
            print('Installed binding execution/replacement passed; scope ' + e.scope['project_id'], flush=True)
        except BaseException:
            e.save('failed')
            raise
        finally:
            e.close()


if __name__ == '__main__':
    main()
