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


def prepare(root, serving, legacy, original, previous, diagnosis, direct, extended, compatible, semantics, reasoning, offline, output):
    output.mkdir(parents=True, exist_ok=True)
    for folder in (original, previous, diagnosis, direct, extended, compatible, semantics, reasoning):
        for name, digest in read(folder / 'frozen-files.json').items():
            assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest
    if (output / 'frozen-files.json').exists():
        for name, digest in read(output / 'frozen-files.json').items():
            assert hashlib.sha256((output / name).read_bytes()).hexdigest() == digest
        print('Additive preparation already frozen; no reset', flush=True)
        return
    diagnostic = read(reasoning / 'supported/response-diagnostic.json')
    exchange = read(reasoning / 'supported/transport-exchange.json')
    assert diagnostic['status'] == 'completed' and diagnostic['incomplete_reason'] is None
    assert read(reasoning / 'supported/current-view.json')['receipt']['phase'] == 'failed'
    assert diagnostic['refused'] is False and exchange['http_status'] == 200
    verification = read(offline)
    assert verification['status'] == 'passed' and verification['profile'] == 'curation-v8'
    assert verification['provider_calls'] == 0
    assert verification['schema_matches_passing_probe'] is True
    assert verification['original_replays'] == 11
    feedback = read(Path(__file__).absolute().parents[2] / 'docs/Audits/Evidence/UI-01.08-Reasoning-Live/proposed-validation-feedback.json')
    assert feedback['public_specification_valid'] and feedback['provider_calls'] == 0
    freeze(output / 'feedback-direction.json', feedback)
    repair = {'diagnostic': diagnostic, 'transport_exchange': exchange,
        'offline': verification, 'profile': 'curation-v8', 'reasoning_effort': 'low',
        'maximum_output_tokens': 8192, 'old_profiles_unchanged': True}
    freeze(output / 'repair-evidence.json', repair)
    evidence = read(serving / 'integrated-evidence.json')
    scope = evidence['scope']
    assert read(original / 'scope-declaration.json')['scope'] == scope
    declaration = dict(read(reasoning / 'scope-declaration.json'), qualification='UI-01.08i-P5-20261012',
        maximum_total_slots=53, maximum_original_units=13300000000,
        maximum_per_call_units=250000000, maximum_output_tokens=8192,
        authorization='UI-01.08i', approved_at_local='2026-10-12 20:47:21',
        previous_declaration_sha256=hashlib.sha256((reasoning / 'scope-declaration.json').read_bytes()).hexdigest())
    freeze(output / 'scope-declaration.json', declaration)
    python = planning_python(serving)
    material_path = output / 'planning-material.json'
    assert owned_process([python, '-I', Path(__file__).with_name('material_feedback.py'), legacy, original, previous, diagnosis, direct, extended, compatible, semantics, reasoning, material_path],
        filtered_environment(), output / 'material.log', timeout=60) == 0
    material = read(material_path)
    prior_material = read(reasoning / 'planning-material.json')
    assert material['instructions'] == prior_material['instructions']
    assert material['generation_schema'] == prior_material['generation_schema']
    assert material['output_schema'] == prior_material['output_schema']
    with session(root, serving) as api:
        retained(api, serving, evidence)
        publication = Publication(api, scope)
        roots_path = output / 'roots.json'
        if not roots_path.exists():
            profile = next(row for row in read(serving / 'artifact.json')['profiles'] if row['media_type'] == 'text/plain')
            schema = {key: profile[key] for key in ('schema_id', 'version', 'sha256')}
            roots = dict(read(reasoning / 'roots.json'))
            roots['configuration'] = publication.publish(
                b'UI-01.08i approved OpenAI gpt-5.4-mini-2026-03-17 direct Responses, reasoning-isolation structured input v8, reasoning low, max output 8192. '
                b'Synthetic egress only. Fifty-three original scope slots and 13.30 USD total holds including thirteen earlier '
                b'reservations; additional 10 USD approved. One new request at a time with 0.25 USD reservation after offline verification. Stop on qualification success or exhausted budget; no blind retry or fallback.', schema)
            # Reuse exact objective, policy and prompt references; only reviewed
            # model configuration changes with the explicit reasoning profile.
            assert all(roots[name] == read(reasoning / 'roots.json')[name]
                       for name in ('objective', 'policy', 'prompt'))
            write(roots_path, roots)
        worker_path = worker_configuration(api, serving, scope, read(roots_path), material, output)
        policy_path = output / 'curation-policy.json'
        policy = read(policy_path)
        policy['policy_id'] = 'internal-curation-feedback-v8'
        policy['template']['context']['limits'].update(max_output_tokens=8192, total_tokens=270336, total_accounting_units=250000000)
        policy['reservation_units'] = 250000000
        write(policy_path, policy)
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
        assert allowance['scope'] == scope and allowance['authorization'] == 'UI-01.08i'
        assert allowance['reserved_slots'] == 13 and allowance['reserved_units'] == 3300000000
        assert allowance['remaining_slots'] == 40 and allowance['remaining_reservation_units'] == 10000000000
        freeze(output / 'live-allowance.json', {'scope': scope, 'diagnostic_stage': 7, 'maximum_new_physical_calls': 1,
            'maximum_new_original_units': 250000000, 'initial': allowance,
            'scenarios': ['supported graph change and successor'],
            'prior_originals_retained': True, 'repair': repair})
        names = ('scope-declaration.json', 'roots.json', 'curation-policy.json', 'curation-worker.json',
                 'initial-allowance.json', 'live-allowance.json', 'planning-material.json', 'repair-evidence.json', 'feedback-direction.json')
        freeze(output / 'frozen-files.json', {name: hashlib.sha256((output / name).read_bytes()).hexdigest() for name in names})
        retained(api, serving, evidence)
    print('Feedback v8 frozen; thirteen old holds retained; first original within additional10 USD; no model key read', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'serving', 'legacy', 'original', 'previous', 'diagnosis', 'direct', 'extended', 'compatible', 'semantics', 'reasoning', 'offline', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    prepare(*(getattr(args, name).absolute() for name in ('root', 'serving', 'legacy', 'original', 'previous', 'diagnosis', 'direct', 'extended', 'compatible', 'semantics', 'reasoning', 'offline', 'output')))
