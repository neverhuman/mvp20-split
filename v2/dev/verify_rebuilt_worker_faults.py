"""Actual restored Runtime/Data: wrong pins, expired fence and wrong policy input."""

import argparse
import json
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from amphora_contracts_core import Scope
from amphora_contracts_runtime import CompleteInvocation
from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState
from amphora_tool_protocol import CommandRejected, HttpTransport, RuntimeClient, WorkerIdentity

from local_demo_controller import Controller
from local_numeric_campaign import Campaign
from local_numeric_configuration import bind_workers, prepare, write


class EvaluationCampaign(Campaign):
    def admit(self, *, wrong_policy=False):
        release = self.releases['evaluate']['tool']
        self.policy = self.publish((self.output / 'policy.json').read_bytes(), release['inputs'][1]['schema_ref'])
        supplied_policy = self.publish((self.output / 'policy.json').read_bytes(), release['inputs'][1]['schema_ref']) if wrong_policy else self.policy
        if wrong_policy:
            assert supplied_policy != self.policy and supplied_policy['sha256'] == self.policy['sha256']
        request = {'schema_version': '1', 'scope': self.scope, 'evaluation_id': 'ev-' + 'a' * 64,
            'specification_sha256': 'f' * 64,
            'candidate': {'candidate_id': 'a' * 64, 'generation': 0, 'ordinal': 0, 'operator': 'seed',
                'genes': [1.0, -2.0], 'parents': [], 'draws': {'start': 0, 'end': 2},
                'disposition': 'proposed', 'reason_code': None, 'duplicate_of': None},
            'objectives': [{'objective_id': name, 'unit': 'dimensionless', 'direction': 'minimize'} for name in ('cost', 'distance')],
            'evaluator': {'tool': release['binding'], 'constraints': self.policy, 'context': [],
                          'completion': 'all_frozen_members_terminal'}}
        parameters = self.publish(json.dumps(request, sort_keys=True, separators=(',', ':')).encode(),
                                  release['inputs'][0]['schema_ref'])
        references = {'parameters': parameters, 'policy': supplied_policy}
        definition = json.loads((self.output / 'graph.json').read_bytes())
        inputs = [{'port': port['name'], 'value': {'kind': 'artifact', 'artifact': references[port['name']],
                  'representation': port['value_type']['representation'], 'unit': port['value_type']['unit']}}
                  for port in definition['body']['inputs']]
        self.admission_command = self.identity('graph.admit', {'plan_sha256': self.plan['sha256'], 'inputs': inputs,
            'budget': {'limit': 16, 'max_attempts_per_activation': 2}})
        self.admission_path = '/v1/graph-runs'
        self.admission = self.call('runtime', self.admission_path, self.admission_command)
        assert self.admission['outcome']['status'] == 'accepted'
        self.run_id = self.admission['outcome']['committed']['object_id']
        return self.run_id

    def result(self):
        page = self.call('runtime', '/v1/graph-observations/' + self.run_id + '/nodes?limit=100')
        invoke, = [row for row in page['nodes'] if row['kind'] == 'invoke']
        token = quote(page['snapshot']['snapshot_token'], safe='')
        detail = self.call('runtime', '/v1/graph-observations/' + self.run_id + '/nodes/' + invoke['activation_id'] + '?snapshot_token=' + token)
        completions = [self.call('runtime', '/v1/runs/' + self.run_id + '/completions/' + row['completion_id'])
                       for row in detail['attempts'] if row['completion_id']]
        return {'graph': self.graph(), 'attempts': detail['attempts'], 'completions': completions}


def single_graph(configuration, material):
    tool = json.loads((configuration / 'evaluate-descriptor.json').read_bytes())['tool']
    def port(item):
        return {'name': item['name'], 'value_type': {'kind': 'artifact', 'media_type': 'application/json',
            **{key: item[key] for key in ('schema_ref', 'representation', 'unit')}}}
    body = {'inputs': [port(item) for item in tool['inputs']], 'outputs': [port(tool['outputs'][0])],
        'nodes': [{'kind': 'invoke', 'node_id': 'evaluate', 'tool': tool['binding'], 'timeout_seconds': 60,
                   'inputs': [{'port': item['name'], 'source': {'kind': 'input', 'name': item['name']}} for item in tool['inputs']]},
                  {'kind': 'finish', 'node_id': 'finish', 'outputs': [{'port': 'result',
                    'source': {'kind': 'output', 'node_id': 'evaluate', 'port': 'result'}}]}],
        'edges': [{'source': 'evaluate', 'target': 'finish', 'route': 'next'}]}
    write(configuration / 'graph.json', {'schema_version': '4', 'profile': 'deterministic-v3',
        'scope': material['scope'], 'campaign_id': 'numeric-search-fixture', 'revision': 1, 'context': [], 'body': body})


def scenario(root, output, bundle, materials, source_manifest, *, wrong_policy):
    original = LocalState.snapshot(root)
    routes = Routes.load(root)
    material, identity, ports = prepare(output, bundle, materials, source_manifest, original['deployment_id'], routes,
        project='replacement-fault-' + uuid.uuid4().hex, delivery=True)
    single_graph(output, material)
    bind_workers(output, bundle, material, identity, ports, 'awaiting-admission', 'standby')
    owners = json.loads((output / 'owners.json').read_bytes())['owners']
    python = Path(owners['runtime']['installation']) / 'environment/Scripts/python.exe'
    tokens = CredentialVault(root / 'credentials.dpapi', original['deployment_id']).load().environment([
        'REGISTRY_OPERATOR_TOKEN', 'RUNTIME_OPERATOR_TOKEN', 'ARTIFACT_OPERATOR_TOKEN', 'RUNTIME_ARTIFACT_TOKEN', 'WORKER_RUNTIME_TOKEN'])
    controller, campaign, drained = None, None, False
    try:
        controller = Controller(root, output, routes, 'standby')
        campaign = EvaluationCampaign(controller, output, material, tokens, python)
        controller.start_owners(tokens['REGISTRY_OPERATOR_TOKEN'])
        run = campaign.admit(wrong_policy=wrong_policy)
        write(output / 'admission.json', {'run_id': run, 'scope': material['scope'], 'command': campaign.admission_command, 'receipt': campaign.admission})
        controller.drain()
        controller.close()
        controller = None
        bind_workers(output, bundle, material, identity, ports, run, 'admitted')
        controller = Controller(root, output, routes, 'admitted')
        campaign.controller = controller
        controller.start_owners(tokens['REGISTRY_OPERATOR_TOKEN'])
        for name in ('runtime-coordinate', 'runtime-deliver'):
            controller.control('/workers/' + name + '/start', 'POST')
        runtime = RuntimeClient(HttpTransport(routes.endpoint('runtime'), tokens['WORKER_RUNTIME_TOKEN']),
            WorkerIdentity('science-slot', Scope.model_validate(material['scope'])))
        controller.wait(lambda: len(runtime.run(run).activations) == 1)
        pin = runtime.identity  # Identity remains the configured worker, never admin authority.
        from amphora_contracts_tools import ToolBinding
        binding = ToolBinding.model_validate_json(json.dumps(campaign.releases['evaluate']['tool']['binding']))
        rejected_pins = []
        first = None
        if not wrong_policy:
            before = campaign.graph()
            for name, changed in [('old_release', binding.model_copy(update={'release': '0.3.0',
                    'image_sha256': 'b6d73b31058d358a5a2a13e44979e8b6e3a6acd06260670226a1b2570f1135e3'})),
                    ('wrong_image', binding.model_copy(update={'image_sha256': '0' * 64}))]:
                receipt = runtime.claim(run, changed, 'probe-' + uuid.uuid4().hex, lease_seconds=10)
                assert receipt.outcome.status == 'no_eligible_work'
                assert campaign.graph() == before
                rejected_pins.append({'case': name, 'receipt': receipt.model_dump(mode='json')})
            # Keep the run active until the stale result has exercised fencing.
            # A terminal-run rejection alone would not prove the fence boundary.
            controller.control('/workers/runtime-coordinate/quiesce', 'POST')
            controller.wait(lambda: controller.control('/status')['workers']['runtime-coordinate']['state'] == 'quiescent')
            first = runtime.claim(run, binding, 'probe-' + uuid.uuid4().hex, lease_seconds=10)
            assert first.outcome.status == 'claimed' and runtime.identity == pin
            delay = (datetime.fromisoformat(first.outcome.lease_expires_at) - datetime.now(UTC)).total_seconds() + .2
            assert 0 < delay <= 11
            time.sleep(delay)
        controller.control('/scientific-workers/synthetic-objectives-rebuilt/start', 'POST')
        if wrong_policy:
            controller.wait(lambda: campaign.graph()['status'] != 'running', timeout=90)
        else:
            # Active-only worker snapshot is one atomic read. Paged graph inspection
            # legitimately invalidates its token during claim/renew/commit changes.
            controller.wait(lambda: not runtime.run(run).activations, timeout=90)
        controller.control('/scientific-workers/synthetic-objectives-rebuilt/quiesce', 'POST')
        controller.wait(lambda: not controller.control('/status')['scientific_workers']['synthetic-objectives-rebuilt']['active_turn'])
        result = campaign.result()
        completion, = result['completions']
        late_reason = None
        if wrong_policy:
            assert result['graph']['status'] == 'blocked' and result['graph']['spent'] == 1
            assert completion['result']['outcome'] == {'status': 'failed', 'reason_code': 'invalid_synthetic_objective_input', 'retryable': False}
        else:
            assert result['graph']['status'] == 'running' and result['graph']['spent'] == 2
            assert sorted(row['status'] for row in result['attempts']) == ['expired', 'succeeded']
            accepted, = [row for row in result['attempts'] if row['canonical_result']]
            assert accepted['fence'] == first.outcome.invocation.fence + 1
            observation = campaign.artifact_bytes(completion['result']['outcome']['outputs'][0]['artifact'])
            assert [item['value'] for item in observation['outcome']['objectives']] == [5.0, 9.0]
            stale = first.outcome.invocation
            payload = CompleteInvocation.model_validate_json(json.dumps({'run_id': run, 'completion': {
                'schema_version': '1', 'invocation_id': stale.invocation_id, 'attempt_id': stale.attempt_id,
                'fence': stale.fence, 'outcome': {'status': 'failed', 'reason_code': 'late_test_result', 'retryable': False}}}))
            try:
                runtime.complete(payload, 'late-' + uuid.uuid4().hex)
            except CommandRejected as error:
                late_reason = error.reason_code
            write(output / 'late-rejection.json', {'reason': late_reason, 'graph': campaign.graph()})
            assert late_reason == 'stale_attempt'
            assert campaign.result() == result
            controller.control('/workers/runtime-coordinate/start', 'POST')
            controller.wait(lambda: campaign.graph()['status'] == 'completed')
            result = campaign.result()
        final = controller.drain()
        drained = True
        assert LocalState.snapshot(root) == original
        write(output / 'evidence.json', {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'passed', 'scenario': 'wrong_policy' if wrong_policy else 'stale_worker', 'run_id': run,
            'pins': rejected_pins, 'first_claim': first.model_dump(mode='json') if first else None,
            'late_rejection': late_reason, 'result': result, 'final': final, 'provider_calls': 0})
        print(('Wrong actual policy identity' if wrong_policy else 'Wrong pins and expired worker fence') + ' rejected; peers drained', flush=True)
    finally:
        if controller is not None:
            try:
                if not drained:
                    if campaign is not None:
                        campaign.cancel_after_failure()
                    controller.drain()
            finally:
                controller.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'output', 'bundle', 'materials', 'source-manifest'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--wrong-policy', action='store_true')
    args = parser.parse_args()
    scenario(*(getattr(args, name).absolute() for name in ('root', 'output', 'bundle', 'materials', 'source_manifest')),
             wrong_policy=args.wrong_policy)
