"""One explicitly selected live scenario under the original frozen scope allowance."""
import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

from amphora_contracts_campaign_curation import CampaignCurationDraft
from amphora_deployment.lifecycle import ProcessJob
from campaign_curation_fixture.campaign import Campaign
from campaign_curation_fixture.recovery import read, retained
from campaign_curation_fixture.session import session
from local_numeric_configuration import write
from .configuration import planning_python, worker_environment

DIRECTIONS = {
    'supported': 'Create one revised synthetic engineering campaign. Keep the single numeric.search-seed invocation, '
        'its exact installed tool binding and existing parameters artifact. Keep the result export. '
        'Add a required root input named previous_result with exactly the same value type as the existing result output. '
        'Add a root output named previous_result of that type and bind that finish output directly to the root input. '
        'The operator will carry the predecessor result into this input through Runtime successor admission. '
        'Retain the seed-to-finish control edge. Use the exact future campaign revision/context from the reviewed declaration. '
        'This is a data-carry software test only, not chemistry or a scientific improvement. Return the complete revised graph.',
    'missing': 'Plan a synthetic research process that combines two molecular components, heats the combined mixture, '
        'then adds a third component. No actual laboratory operation or chemical protocol is requested. '
        'The installed numeric seed/evaluator tools cannot perform these molecular or mixture operations. '
        'Identify the missing typed capabilities, their applicability, expected evidence and acceptance criteria. '
        'Do not substitute a numeric search tool or invent an installed release. Return structured missing-capability '
        'requests when the inventory cannot express this process. Do not claim that a requested tool is fulfilled.',
}


def credential(path):
    key = os.environ.get('OPENAI_API_KEY')
    if key:
        return key
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        name, separator, value = line.partition('=')
        if separator and name.strip() == 'OPENAI_API_KEY':
            key = value.strip().strip('"').strip("'")
            if key:
                return key
    raise ValueError('openai_credentials_missing')


def owned_process(command, environment, log_path, timeout=300):
    job, process = ProcessJob(), None
    try:
        with log_path.open('a', encoding='utf-8') as log:
            process = subprocess.Popen([str(item) for item in command], env=environment, stdout=log, stderr=log,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            job.attach(process)
            return process.wait(timeout=timeout)
    finally:
        job.close()
        if process is not None:
            process.wait(timeout=10)


def verify(root, serving, qualification, scenario, key_file):
    for name, digest in read(qualification / 'frozen-files.json').items():
        assert hashlib.sha256((qualification / name).read_bytes()).hexdigest() == digest, 'Frozen live preparation changed'
    declaration = read(qualification / 'scope-declaration.json')
    allowance = read(qualification / 'live-allowance.json')
    if declaration['authorization'] == 'UI-01.08g':
        assert scenario == 'supported' and allowance['maximum_new_physical_calls'] == 1
        assert allowance['diagnostic_stage'] == 5 and allowance['initial']['reserved_slots'] == 11
        assert allowance['initial']['reserved_units'] == 2800000000
        assert declaration['maximum_total_slots'] == 12 and declaration['maximum_original_units'] == 3050000000
        assert declaration['maximum_per_call_units'] == 250000000 and declaration['maximum_output_tokens'] == 8192
        assert allowance['maximum_new_original_units'] == 250000000
        repair = read(qualification / 'repair-evidence.json')
        assert repair == allowance['repair'] and repair['profile'] == 'curation-v7'
        assert repair['maximum_output_tokens'] == 8192 and repair['reasoning_effort'] == 'none'
        assert repair['offline']['status'] == 'passed' and repair['offline']['provider_calls'] == 0
        assert repair['offline']['schema_matches_passing_probe'] is True and repair['offline']['original_replays'] == 9
    elif declaration['authorization'] == 'UI-01.08f':
        assert scenario == 'supported' and allowance['maximum_new_physical_calls'] == 1
        assert allowance['diagnostic_stage'] == 4 and allowance['initial']['reserved_slots'] == 10
        assert allowance['initial']['reserved_units'] == 2550000000
        assert declaration['maximum_total_slots'] == 11 and declaration['maximum_original_units'] == 2800000000
        assert declaration['maximum_per_call_units'] == 250000000 and declaration['maximum_output_tokens'] == 8192
        assert allowance['maximum_new_original_units'] == 250000000
        repair = read(qualification / 'repair-evidence.json')
        assert repair == allowance['repair'] and repair['profile'] == 'curation-v6'
        assert repair['maximum_output_tokens'] == 8192 and repair['reasoning_effort'] == 'none'
        assert repair['offline']['status'] == 'passed' and repair['offline']['provider_calls'] == 0
        assert repair['offline']['schema_matches_passing_probe'] is True and repair['offline']['original_replays'] == 8
    elif declaration['authorization'] == 'UI-01.08d':
        assert scenario == 'supported' and allowance['maximum_new_physical_calls'] == 1
        assert allowance['diagnostic_stage'] == 3 and allowance['initial']['reserved_slots'] == 9
        assert declaration['maximum_total_slots'] == 10 and declaration['maximum_original_units'] == 2550000000
        assert declaration['maximum_per_call_units'] == 300000000 and declaration['maximum_output_tokens'] == 16384
        assert allowance['maximum_new_original_units'] == 300000000
        repair = read(qualification / 'repair-evidence.json')
        assert repair == allowance['repair'] and repair['profile'] == 'curation-v5'
        assert repair['maximum_output_tokens'] == 16384 and repair['reasoning_effort'] == 'none'
        assert repair['diagnostic']['incomplete_reason'] == 'max_output_tokens'
        assert repair['offline']['status'] == 'passed' and repair['offline']['provider_calls'] == 0
    elif declaration['authorization'] == 'UI-01.08c':
        assert scenario == 'supported' and allowance['maximum_new_physical_calls'] == 1
        if allowance['diagnostic_stage'] == 1:
            assert allowance['initial']['reserved_slots'] == 7
        else:
            assert allowance['diagnostic_stage'] == 2 and allowance['initial']['reserved_slots'] == 8
            repair = read(qualification / 'repair-evidence.json')
            assert allowance['repair'] == repair and repair['profile'] == 'curation-v4'
            assert repair['diagnostic']['incomplete_reason'] == 'max_output_tokens'
            assert repair['offline']['status'] == 'passed' and repair['offline']['provider_calls'] == 0
            assert repair['reasoning_effort'] == 'none' and repair['maximum_output_tokens'] == 8192
        assert declaration['maximum_total_slots'] == 9 and declaration['maximum_original_units'] == 2250000000
        assert allowance['maximum_new_original_units'] == 250000000
    elif declaration['authorization'] == 'UI-01.08b':
        assert scenario == 'supported' and allowance['maximum_new_physical_calls'] == 1
        assert declaration['maximum_total_slots'] == 7 and declaration['maximum_original_units'] == 1750000000
        assert allowance['maximum_new_original_units'] == 250000000
    else:
        assert allowance['maximum_new_physical_calls'] == 2
        assert declaration['maximum_total_slots'] == 4 or (
            declaration['maximum_total_slots'] == 6 and declaration['maximum_original_units'] == 1500000000
            and declaration['authorization'] == 'UI-01.08a')
    original = read(serving / 'integrated-evidence.json')
    scope = original['scope']
    assert scope == declaration['scope'] == allowance['scope']
    output = qualification / scenario
    output.mkdir(exist_ok=True)
    with session(root, serving) as api:
        retained(api, serving, original)
        campaign = Campaign(api, output, scope)
        draft = read(serving / 'original-draft.json')['head']
        sources = read(serving / 'original-carry-sources.json')
        command = campaign.original('curation', 'planning.curate_campaign', {
            'direction': DIRECTIONS[scenario], 'policy_id': read(qualification / 'curation-policy.json')['policy_id'],
            'context': {'predecessor': sources['predecessor'], 'draft': {'scope': scope,
                **{key: draft[key] for key in ('draft_id', 'revision', 'content_sha256')}},
                'knowledge': [], 'questions': [], 'needs': [],
                'artifacts': [read(serving / 'published-case.json')['specification']]}})
        receipt = api.call('planning', '/v1/campaign-curations', command, allowed=(200, 202))
        write(output / 'original-receipt.json', receipt)
        curation_id = receipt['reference']['curation_id']
        path = '/v1/campaign-curations/' + curation_id
        current = api.call('planning', path)
        terminal = current['receipt']['phase'] in {'ready', 'failed', 'indeterminate', 'abstained'} or (
            current['proposal'] is not None and current['proposal']['outcome']['kind'] == 'request_capabilities')
        if not terminal:
            environment = worker_environment(root, api)
            python = planning_python(serving)
            config = qualification / 'curation-worker.json'
            assert owned_process([python, '-I', Path(__file__).with_name('allowance.py'), config,
                output / 'allowance-before.json'], environment, output / 'allowance.log', timeout=60) == 0
            before = read(output / 'allowance-before.json')
            assert before['scope'] == scope and before['reserved_slots'] <= declaration['maximum_total_slots']
            # DispatchJournal reconciles any original issued request before considering a new send.
            environment['OPENAI_API_KEY'] = credential(key_file)
            try:
                code = owned_process([python, '-I', Path(__file__).with_name('worker.py'), config, curation_id, output],
                                     environment, output / 'worker.log')
            finally:
                environment.pop('OPENAI_API_KEY', None)
            current = api.call('planning', path)
            write(output / 'current-view.json', current)
            assert code == 0, 'Live worker did not finish; retain original and inspect owned evidence'
        write(output / 'current-view.json', current)
        assert current['provider'] is not None and current['proposal'] is not None, current['receipt']
        raw = (output / 'original-output.json').read_bytes()
        assert hashlib.sha256(raw).hexdigest() == current['provider']['output_sha256']
        assert CampaignCurationDraft.model_validate_json(raw).model_dump(mode='json') == current['proposal']
        if scenario == 'supported':
            assert current['receipt']['phase'] == 'ready' and current['proposal']['outcome']['kind'] == 'propose_campaign'
            selected = current['validated_draft']
            compiled = api.call('runtime', '/v1/definition-drafts/' + selected['draft_id'] + '?revision=' + str(selected['revision']))
            assert compiled['definition'] == current['proposal']['outcome']['candidate']['definition']
            assert [port['name'] for port in compiled['definition']['body']['inputs']] == ['previous_result']
            validation = api.call('runtime', '/v1/definition-validations/' + selected['validation_id'])
            profile = read(serving / 'launch-profile.json')
            write(output / 'launch-profile.json', profile)
            result = next(row for row in sources['sources'] if row['source'] == {'kind': 'run_output', 'port': 'result'})
            carried = [{'target_port': 'previous_result', 'source': result['source'], 'expected_value_sha256': result['value_sha256']}]
            launch, successor, child_sources = campaign.launch(validation, profile['reference'], predecessor=sources['predecessor'], carried=carried)
            lineage = api.call('runtime', '/v1/graph-runs/' + successor['run_id'] + '/lineage')
            assert lineage['predecessor'] == sources['predecessor'] and lineage['carried'] == carried
            exported = next(row for row in child_sources['sources'] if row['source'] == {'kind': 'run_output', 'port': 'previous_result'})
            assert exported['value_sha256'] == result['value_sha256']
            write(output / 'successor-evidence.json', {'launch': launch, 'run': successor, 'lineage': lineage})
        else:
            assert current['proposal']['outcome']['kind'] == 'request_capabilities'
            assert current['validated_draft'] is None and current['capability_requests']
            requests = [api.call('planning', '/v1/capability-requests/' + ref['request_id']) for ref in current['capability_requests']]
            write(output / 'capability-requests.json', requests)
        assert api.call('planning', '/v1/campaign-curations', command, allowed=(200, 202)) == receipt
        retained(api, serving, original)
        write(output / 'evidence.json', {'status': 'passed', 'scenario': scenario,
            'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'curation': current, 'model_output_sha256': hashlib.sha256(raw).hexdigest(),
            'provider': 'actual pinned OpenAI through installed production worker', 'scientific_validity': 'not_established'})
    print('Live ' + scenario + ' owner scenario passed and drained', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--serving', type=Path, required=True)
    parser.add_argument('--qualification', type=Path, required=True)
    parser.add_argument('--scenario', choices=tuple(DIRECTIONS), required=True)
    parser.add_argument('--key-file', type=Path, default=Path('Z:/ssos/.env'))
    args = parser.parse_args()
    verify(args.root.absolute(), args.serving.absolute(), args.qualification.absolute(), args.scenario, args.key_file)
