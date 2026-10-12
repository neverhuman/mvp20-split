"""Additive approved qualification roots; old declarations and captures are immutable."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from campaign_curation_fixture.publication import Publication
from campaign_curation_fixture.recovery import read, retained
from campaign_curation_fixture.session import session
from campaign_curation_fixture.verify import worker_configuration, filtered_environment
from local_numeric_configuration import write
from .configuration import freeze, planning_python, worker_environment
from .run import owned_process


def prepare(root, serving, original, output):
    output.mkdir(parents=True, exist_ok=True)
    for name, digest in read(original / 'frozen-files.json').items():
        assert hashlib.sha256((original / name).read_bytes()).hexdigest() == digest
    if (output / 'frozen-files.json').exists():
        for name, digest in read(output / 'frozen-files.json').items():
            assert hashlib.sha256((output / name).read_bytes()).hexdigest() == digest
        print('Additive preparation already frozen; no reset', flush=True)
        return
    evidence = read(serving / 'integrated-evidence.json')
    scope = evidence['scope']
    assert read(original / 'scope-declaration.json')['scope'] == scope
    declaration = dict(read(original / 'scope-declaration.json'), qualification='UI-01.08a-P5-20261012',
        maximum_total_slots=6, maximum_original_units=1500000000,
        authorization='UI-01.08a', approved_at_local='2026-10-12 08:41:16',
        previous_declaration_sha256=hashlib.sha256((original / 'scope-declaration.json').read_bytes()).hexdigest())
    freeze(output / 'scope-declaration.json', declaration)
    python = planning_python(serving)
    material_path = output / 'planning-material.json'
    assert owned_process([python, '-I', Path(__file__).with_name('material.py'), original, material_path],
        filtered_environment(), output / 'material.log', timeout=60) == 0
    material = read(material_path)
    with session(root, serving) as api:
        retained(api, serving, evidence)
        publication = Publication(api, scope)
        roots_path = output / 'roots.json'
        if not roots_path.exists():
            profile = next(row for row in read(serving / 'artifact.json')['profiles'] if row['media_type'] == 'text/plain')
            schema = {key: profile[key] for key in ('schema_id', 'version', 'sha256')}
            roots = {name: publication.publish(body, schema) for name, body in (
                ('objective', b'Qualify synthetic engineering graph revisions and truthful missing-capability requests.'),
                ('policy', b'Reviewed live-model synthetic engineering qualification only. Graph proposals and capability '
                 b'requests are allowed; no chemical operation, scientific efficacy or authority claim. '
                 b'Preserve exact source pins and all previous campaign history.'),
                ('configuration', b'UI-01.08a approved OpenAI gpt-5.4-mini-2026-03-17 direct Responses, readable input v2. '
                 b'Synthetic egress only. Six original scope slots and 1.50 USD total holds including four earlier '
                 b'reservations; at most two new requests with 0.25 USD each, one attempt, no retry or fallback.'),
                ('prompt', material['instructions'].encode()))}
            write(roots_path, roots)
        worker_path = worker_configuration(api, serving, scope, read(roots_path), material, output)
        policy_path = output / 'curation-policy.json'
        policy = read(policy_path); policy['policy_id'] = 'internal-curation-v2'; write(policy_path, policy)
        config = read(worker_path)
        config.update(provider='openai_curation_v1', live={'key_env': 'OPENAI_API_KEY', 'scope': scope,
            'egress': 'approved_synthetic_engineering_only', 'timeout_seconds': 60})
        write(worker_path, config)
        environment = worker_environment(root, api)
        assert owned_process([python, '-I', '-m', 'amphora_agent_planning.curation_worker', 'check', '--config', worker_path],
            environment, output / 'preparation.log', timeout=60) == 0
        assert owned_process([python, '-I', Path(__file__).with_name('allowance.py'), worker_path, output / 'initial-allowance.json'],
            environment, output / 'preparation.log', timeout=60) == 0
        allowance = read(output / 'initial-allowance.json')
        assert allowance['scope'] == scope and allowance['authorization'] == 'UI-01.08a'
        assert allowance['reserved_slots'] == 4 and allowance['reserved_units'] == 1000000000
        assert allowance['remaining_slots'] == 2 and allowance['remaining_reservation_units'] == 500000000
        freeze(output / 'live-allowance.json', {'scope': scope, 'maximum_new_physical_calls': 2,
            'maximum_new_original_units': 500000000, 'initial': allowance,
            'scenarios': ['supported graph change and successor', 'missing capability'],
            'prior_originals_retained': True})
        names = ('scope-declaration.json', 'roots.json', 'curation-policy.json', 'curation-worker.json',
                 'initial-allowance.json', 'live-allowance.json', 'planning-material.json')
        freeze(output / 'frozen-files.json', {name: hashlib.sha256((output / name).read_bytes()).hexdigest() for name in names})
        retained(api, serving, evidence)
    print('Additive v2 roots frozen; original four holds retained and two approved slots remain; no model key read', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'serving', 'original', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    prepare(*(getattr(args, name).absolute() for name in ('root', 'serving', 'original', 'output')))
