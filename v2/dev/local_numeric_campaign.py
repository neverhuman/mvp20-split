"""Public-API synthetic campaign fixture; authoritative execution stays in Runtime."""

import hashlib
import importlib.util
import json
import os
import subprocess
import urllib.parse
import urllib.request
import uuid
from pathlib import Path


class Campaign:
    def __init__(self, controller, output, material, tokens, runtime_python, *, fixture_root=None):
        self.controller, self.output, self.material, self.tokens = controller, output, material, tokens
        self.scope, self.run_id = material['scope'], None
        self.releases = {stage: json.loads((output / (stage + '-descriptor.json')).read_bytes()) for stage in material['locks']}
        self.fixture_root = Path(__file__).absolute().parents[1] if fixture_root is None else fixture_root
        script = self.fixture_root / 'services/campaign_runtime/tests/scheduling/acceptance/compile_plans.py'
        environment = {key: value for key, value in os.environ.items() if key.upper() in {
            'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
        result = subprocess.run([str(runtime_python), '-I', str(script), str(output / 'runtime.json')],
            env=environment, capture_output=True, timeout=30)
        assert result.returncode == 0, 'Owner-local test compiler failed'
        self.plan = json.loads(result.stdout)['numeric-search-fixture']
        self.compiler_probe_sha256 = hashlib.sha256(script.read_bytes()).hexdigest()

    def identity(self, family, payload):
        return {'identity': {'scope': self.scope, 'actor_id': 'admin', 'command_id': uuid.uuid4().hex,
                             'command_family': family}, 'payload': payload}

    def call(self, owner, path, body=None, *, method=None, reference=None):
        reference = reference or owner.upper() + '_OPERATOR_TOKEN'
        code, value = self.controller.request(self.controller.routes.endpoint(owner), path,
            token=self.tokens[reference], body=body, method=method)
        assert code == 200, 'Public demo API failed: ' + owner + ' ' + path + ' ' + str(code)
        return value

    def publish(self, body, schema):
        content = {'sha256': hashlib.sha256(body).hexdigest(), 'size_bytes': len(body),
                   'media_type': 'application/json', 'schema_ref': schema}
        upload = self.call('artifact', '/v1/uploads', self.identity('artifacts.begin_upload', {'content': content}))
        self.call('artifact', '/v1/uploads/' + upload['upload_id'] + '/content', body, method='PUT')
        result = self.call('artifact', '/v1/artifacts/finalize',
            self.identity('artifacts.finalize', {'upload_id': upload['upload_id'], 'content': content}))
        return result['artifact']

    def admit(self):
        self.policy = self.publish((self.output / 'policy.json').read_bytes(),
                                  self.releases['evaluate']['tool']['inputs'][1]['schema_ref'])
        script = self.fixture_root / 'services/campaign_runtime/tests/numeric_search/specification.py'
        spec = importlib.util.spec_from_file_location('local_demo_specification', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.specification = module.specification(self.scope, self.releases, self.policy)
        body = json.dumps(self.specification, sort_keys=True, separators=(',', ':')).encode()
        artifact = self.publish(body, self.releases['seed']['tool']['inputs'][0]['schema_ref'])
        definition = json.loads((self.output / 'graph.json').read_bytes())
        refs = {'specification': artifact, 'policy': self.policy}
        inputs = [{'port': port['name'], 'value': {'kind': 'artifact', 'artifact': refs[port['name']],
            'representation': port['value_type']['representation'], 'unit': port['value_type']['unit']}}
            for port in definition['body']['inputs']]
        self.admission_command = self.identity('graph.admit', {'plan_sha256': self.plan['sha256'], 'inputs': inputs,
                                                'budget': {'limit': 256, 'max_attempts_per_activation': 2}})
        self.admission = self.call('runtime', '/v1/graph-runs', self.admission_command)
        assert self.admission['outcome']['status'] == 'accepted', self.admission['outcome']
        self.run_id = self.admission['outcome']['committed']['object_id']
        return self.run_id

    def graph(self):
        return self.call('runtime', '/v3/graph-runs/' + self.run_id)

    def artifact_bytes(self, artifact):
        request = urllib.request.Request(self.controller.routes.endpoint('artifact') + '/v1/artifacts/' +
            artifact['artifact_id'] + '/content', headers={'Authorization': 'Bearer ' + self.tokens['ARTIFACT_OPERATOR_TOKEN']})
        with self.controller.opener.open(request, timeout=3) as response:
            raw = response.read(262145)
            assert response.status == 200 and len(raw) == artifact['size_bytes']
            assert hashlib.sha256(raw).hexdigest() == artifact['sha256']
            return json.loads(raw)

    def evidence(self):
        graph = self.graph()
        assert graph['status'] == 'completed' and graph['reserved'] == 0 and graph['spent'] == 15
        page = self.call('runtime', '/v1/graph-observations/' + self.run_id + '/nodes?limit=100')
        assert page['next_cursor'] is None
        token = urllib.parse.quote(page['snapshot']['snapshot_token'], safe='')
        reports = []
        for node in page['nodes']:
            if node['kind'] != 'invoke':
                continue
            detail = self.call('runtime', '/v1/graph-observations/' + self.run_id + '/nodes/' +
                node['activation_id'] + '?snapshot_token=' + token)
            assert detail['next_cursor'] is None
            canonical = [row for row in detail['attempts'] if row['canonical_result']]
            assert len(canonical) == 1 and canonical[0]['status'] == 'succeeded'
            completion = self.call('runtime', '/v1/runs/' + self.run_id + '/completions/' + canonical[0]['completion_id'])
            assert completion['canonical_result'] and len(completion['retention_reservation_ids']) == 1
            artifact = completion['result']['outcome']['outputs'][0]['artifact']
            result = self.artifact_bytes(artifact)
            reports.append({'completion': completion, 'artifact': artifact, 'result': result})
        assert len(reports) == 15
        checkpoints = sorted([report for report in reports if report['artifact']['schema_ref']['schema_id'] == 'search.checkpoint'
            and report['result']['phase'] in ('selected', 'stopped')], key=lambda report: report['result']['generation'])
        assert [row['result']['generation'] for row in checkpoints] == [0, 1, 2]
        final = checkpoints[-1]['result']
        assert final['stop_reason'] == 'generation_budget' and final['rng']['counter'] == 26
        evaluations = [report for report in reports if report['artifact']['schema_ref']['schema_id'] == 'search.evaluation-observation']
        assert len(evaluations) == 6 == final['progress']['evaluations_issued']
        assert all(report['result']['outcome']['evidence'] == [self.policy] for report in evaluations)
        retained = {}
        (self.output / 'canonical-completions.json').write_text(json.dumps(reports, indent=2) + '\n', encoding='utf-8')
        last = {}
        def confirmed():
            for report in reports:
                for reservation in report['completion']['retention_reservation_ids']:
                    retained[reservation] = self.call('artifact', '/v1/reservations/' + reservation,
                                                     reference='RUNTIME_ARTIFACT_TOKEN')
            statuses = {key: value['outcome']['status'] for key, value in retained.items()}
            if statuses != last:
                (self.output / 'retention-progress.json').write_text(json.dumps(retained, indent=2) + '\n', encoding='utf-8')
                last.clear()
                last.update(statuses)
            return all(value == 'confirmed' for value in statuses.values())
        self.controller.wait(confirmed, timeout=120)
        assert self.call('runtime', '/v1/graph-runs', self.admission_command) == self.admission
        return {'graph': graph, 'admission': self.admission, 'reports': reports, 'retained': retained,
                'compiler_probe_sha256': self.compiler_probe_sha256}

    def cancel_after_failure(self):
        if self.run_id is not None:
            return self.call('runtime', '/v1/runs/cancel', self.identity('runtime.cancel',
                {'run_id': self.run_id, 'reason_code': 'local_demo_probe_failed'}))
