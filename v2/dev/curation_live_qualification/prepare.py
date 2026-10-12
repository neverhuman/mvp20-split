"""Freeze synthetic live qualification without reading a key or making a provider call."""
import argparse
import hashlib
import subprocess
from pathlib import Path

from campaign_curation_fixture.publication import Publication
from campaign_curation_fixture.recovery import read
from campaign_curation_fixture.session import session
from campaign_curation_fixture.verify import worker_configuration
from local_numeric_configuration import write
from .configuration import freeze, planning_python, worker_environment


def prepare(root, serving, output):
    output.mkdir(parents=True, exist_ok=True)
    if (output / 'frozen-files.json').exists():
        for name, digest in read(output / 'frozen-files.json').items():
            assert hashlib.sha256((output / name).read_bytes()).hexdigest() == digest, 'Frozen live configuration changed'
        print('Original live preparation retained; no rewrites or allowance reset', flush=True)
        return
    original = read(serving / 'integrated-evidence.json')
    assert original['status'] == 'passed' and read(serving / 'recovery-evidence.json')['status'] == 'passed'
    scope = original['scope']
    freeze(output / 'scope-declaration.json', {'qualification': 'UI-01.08-P5-20261012',
        'scope': scope, 'maximum_total_slots': 4, 'maximum_original_units': 1000000000,
        'maximum_per_call_units': 250000000, 'unit': 'usd_nanodollars',
        'model': 'gpt-5.4-mini-2026-03-17', 'endpoint': 'https://api.openai.com/v1/responses',
        'egress': 'approved_synthetic_engineering_only', 'automatic_retries': 0,
        'other_scopes_authorized': False, 'prior_synthetic_holds_count': True})
    with session(root, serving) as api:
        publication = Publication(api, scope)
        roots_path = output / 'roots.json'
        if not roots_path.exists():
            roots = read(serving / 'published-case.json')['roots']
            profile = next(row for row in read(serving / 'artifact.json')['profiles'] if row['media_type'] == 'text/plain')
            schema = {key: profile[key] for key in ('schema_id', 'version', 'sha256')}
            roots['configuration'] = publication.publish(
                b'Reviewed live OpenAI gpt-5.4-mini-2026-03-17 Responses qualification. '
                b'Only published synthetic engineering context may leave this machine. '
                b'One original call per request; no retry, alternate model or fabricated response. '
                b'Four scope slots and one USD maximum original holds, including earlier synthetic reservations.', schema)
            write(roots_path, roots)
        worker_path = worker_configuration(api, serving, scope, read(roots_path), read(serving / 'planning-material.json'), output)
        config = read(worker_path)
        config.update(provider='openai_curation_v1', live={'key_env': 'OPENAI_API_KEY', 'scope': scope,
            'egress': 'approved_synthetic_engineering_only', 'timeout_seconds': 60})
        write(worker_path, config)
        env = worker_environment(root, api)
        python = planning_python(serving)
        with (output / 'preparation.log').open('a', encoding='utf-8') as log:
            result = subprocess.run([str(python), '-I', '-m', 'amphora_agent_planning.curation_worker',
                'check', '--config', str(worker_path)], env=env, stdout=log, stderr=log, timeout=60,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            assert result.returncode == 0, 'Installed live configuration check failed'
            report = output / 'initial-allowance.json'
            result = subprocess.run([str(python), '-I', str(Path(__file__).with_name('allowance.py')),
                str(worker_path), str(report)], env=env, stdout=log, stderr=log, timeout=60,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            assert result.returncode == 0, 'Installed read-only allowance check failed'
        allowance = read(report)
        assert allowance['scope'] == scope and allowance['reserved_slots'] == 2 and allowance['reserved_units'] == 500000000
        assert allowance['remaining_slots'] == 2 and allowance['remaining_reservation_units'] == 500000000
        freeze(output / 'live-allowance.json', {'scope': scope, 'maximum_new_physical_calls': 2,
            'maximum_new_original_units': 500000000, 'initial': allowance,
            'scenarios': ['supported graph change and successor', 'missing capability'],
            'paid_calls_so_far': 0, 'key_read': False})
        freeze(output / 'frozen-files.json', {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
            for name in ('scope-declaration.json', 'roots.json', 'curation-policy.json',
                         'curation-worker.json', 'initial-allowance.json', 'live-allowance.json')})
    print('Synthetic live scope/configuration frozen; two original slots remain; no key/provider call', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--serving', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.root.absolute(), args.serving.absolute(), args.output.absolute())
