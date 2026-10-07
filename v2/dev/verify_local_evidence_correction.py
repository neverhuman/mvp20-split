"""Public future-only source/Knowledge correction on retained local owners; no model calls."""

import argparse
import copy
import hashlib
import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState

from local_authoring_controller import AuthoringController
from local_numeric_configuration import write
from verify_local_owner_records import Scenario
from verify_local_successor import Requests


class CorrectionScenario(Scenario):
    """Persist each original public request before delivery; never replace its identity."""

    def retained_call(self, name, owner, path, body, method=None):
        intent = self.output / (name + '-request.json')
        if intent.exists():
            assert json.loads(intent.read_bytes()) == body, 'Correction intent changed'
        else:
            write(intent, body)
        result = self.call(owner, path, body, method=method)
        receipt = self.output / (name + '-response.json')
        if receipt.exists():
            assert json.loads(receipt.read_bytes()) == result, 'Correction replay changed'
        else:
            write(receipt, result)
        return result

    def publish_content(self, content, schema, media_type, identity, name):
        descriptor = {'sha256': hashlib.sha256(content).hexdigest(), 'size_bytes': len(content),
                      'media_type': media_type, 'schema_ref': schema}
        def command(family, payload, suffix):
            return {'identity': {'scope': self.scope, 'actor_id': 'admin',
                    'command_id': identity + '-' + name + suffix, 'command_family': family}, 'payload': payload}
        upload = self.retained_call(name + '-upload', 'artifact', '/v1/uploads',
            command('artifacts.begin_upload', {'content': descriptor}, '-upload'))
        finalized = self.output / (name + '-finalize-response.json')
        if not finalized.exists():
            self.call('artifact', '/v1/uploads/' + upload['upload_id'] + '/content', content, method='PUT')
        return self.retained_call(name + '-finalize', 'artifact', '/v1/artifacts/finalize',
            command('artifacts.finalize', {'upload_id': upload['upload_id'], 'content': descriptor}, '-finalize'))['artifact']


def prepare(source, records, output):
    output.mkdir(parents=True, exist_ok=False)
    for path in source.glob('*.json'):
        shutil.copyfile(path, output / path.name)
    owners = json.loads((source / 'owners.json').read_bytes())['owners']
    prior_path = Path(owners['artifact']['configuration'])
    data = json.loads(prior_path.read_bytes())
    for row in data['profiles']:
        if 'schema_path' in row:
            row['schema_path'] = str((prior_path.parent / row['schema_path']).absolute())
    data['acquisition'] = True
    principal = next(row for row in data['principals'] if row['token_env'] == 'AMPHORA_ARTIFACT_OPERATOR_TOKEN')
    for action in ('acquire', 'source_history', 'manage_source_rights'):
        if action not in principal['actions']:
            principal['actions'].append(action)
    owners['artifact']['configuration'] = str(write(output / 'correction-artifact.json', data))
    write(output / 'owners.json', {'profile': 'local-supervisor-v1', 'owners': owners})
    write(output / 'correction-intent.json', {'identity': uuid.uuid4().hex, 'records': str(records),
        'statement': 'Corrected synthetic result interpretation: this numeric fixture demonstrates bounded software execution only. Improvement beyond the fixture and biological applicability remain unresolved; no scientific validation is claimed.'})


def verify(source, records_path, retained, output, resume=False):
    if not resume:
        prepare(source, records_path, output)
    intent = json.loads((output / 'correction-intent.json').read_bytes())
    records = json.loads(Path(intent['records']).read_bytes())
    old = json.loads((retained / 'evidence.json').read_bytes())
    scope = old['scope']
    root = Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation'
    state, vault = LocalState.snapshot(root), (root / 'credentials.dpapi').read_bytes()
    routes = Routes.load(root)
    tokens = CredentialVault(root / 'credentials.dpapi', state['deployment_id']).load().environment(
        [owner + '_OPERATOR_TOKEN' for owner in ('ARTIFACT', 'RESEARCH', 'KNOWLEDGE', 'RUNTIME', 'REGISTRY')])
    controller = AuthoringController(root, output, routes, registry_token=tokens['REGISTRY_OPERATOR_TOKEN'])
    try:
        controller.start()
        scenario = CorrectionScenario(controller, tokens, scope, output)
        runtime = Requests(controller, routes, tokens['RUNTIME_OPERATOR_TOKEN'], scope, output)
        before = runtime.read('/v3/graph-runs/' + old['run_id'])
        before_file = output / 'original-run.json'
        if before_file.exists():
            assert json.loads(before_file.read_bytes()) == before
        else:
            write(before_file, before)
        schema = {'schema_id': 'demo.text', 'version': '1', 'sha256': hashlib.sha256(b'{"type":"string"}').hexdigest()}
        artifact = scenario.publish_content(intent['statement'].encode(), schema, 'text/plain', intent['identity'], 'text')
        source_record = copy.deepcopy(records['source'])
        source_record.update(reference=dict(source_record['reference'], revision_id='r2', raw=artifact),
            supersedes=records['source']['reference'], delivery=dict(source_record['delivery'], delivery_id='correction-' + intent['identity']))
        prepared = scenario.retained_call('source-prepare', 'artifact', '/v1/acquisition/prepare', source_record)
        converted = scenario.publish_content(prepared['content_json_utf8'].encode(), prepared['schema_ref'],
            'application/json', intent['identity'], 'converted')
        trace = scenario.retained_call('source-retain', 'artifact', '/v1/acquisition/retain',
            {'wire_version': '1', 'source': source_record, 'trace_id': 'correction-' + intent['identity'], 'output': converted})
        original = records['proposal']['operations'][2]['assertion']
        grounding = {'spans': [{'source': source_record['reference'], 'unit': 'byte', 'start': 0,
            'end': artifact['size_bytes'], 'sha256': artifact['sha256']}],
            'conversion_traces': [trace], 'interpretation_artifacts': [artifact]}
        replacement = copy.deepcopy(original)
        replacement.update(reference=dict(original['reference'], revision=2), supersedes=original['reference'],
            statement=intent['statement'], posture='unresolved', applicability=artifact, grounding=grounding)
        replacement['research_links'][0]['answer_proposal'] = artifact
        proposal = copy.deepcopy(records['proposal'])
        proposal.update(change_id='correction-' + intent['identity'], base=records['accepted']['decision']['head'],
            description='Correct interpretation of the retained synthetic result for future campaigns.',
            rationale='A successful fixture is not evidence of scientific improvement; preserve original history.',
            grounding=grounding, operations=[{'operation': 'correct_assertion', 'prior': original['reference'], 'replacement': replacement}])
        accepted = scenario.retained_call('graph-correction', 'knowledge', '/v1/graph-proposals', proposal)
        assert accepted['decision']['outcome'] == 'accepted'
        head = accepted['decision']['head']
        snapshot = scenario.call('knowledge', '/v1/graph-snapshots/read', head['snapshot'])
        assertions = snapshot['content']['assertions']
        assert original in assertions and replacement in assertions and len(assertions) == 2
        assert scenario.call('knowledge', '/v1/graph-snapshots/read', records['snapshot']['reference']) == records['snapshot']
        assert runtime.read('/v3/graph-runs/' + old['run_id']) == before
        rebuild = scenario.retained_call('corrected-rebuild', 'knowledge', '/v1/graph-rebuilds',
            {'wire_version': '1', 'graph': proposal['graph'], 'rebuild_id': 'correction-' + intent['identity']})
        assert rebuild['result']['outcome'] == 'published' and rebuild['result']['head'] == head
        # Historical Research declarations stay exact; no inferred scientific assessment.
        for name, path in [('question', 'questions'), ('need', 'evidence-needs')]:
            assert scenario.call('research', '/v1/' + path + '/read', records[name]['reference']) == records[name]
        final = controller.drain()
        assert LocalState.snapshot(root) == state and (root / 'credentials.dpapi').read_bytes() == vault
        write(output / 'correction-evidence.json', {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'passed', 'scope': scope, 'original_run': before, 'artifact': artifact,
            'source': source_record, 'trace': trace, 'proposal': proposal, 'accepted': accepted,
            'snapshot': snapshot, 'rebuild': rebuild, 'final': final, 'provider_calls': 0,
            'limits': ['Synthetic result-interpretation correction; no measured lab result or scientific assessment',
                'Original campaign and snapshot unchanged; corrected successor admission remains a separate checkpoint']})
        print('Actual source/Knowledge correction and accepted-log rebuild passed; original campaign unchanged', flush=True)
    finally:
        controller.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'records', 'retained', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    verify(*(getattr(args, name).absolute() for name in ('source', 'records', 'retained', 'output')), resume=args.resume)
