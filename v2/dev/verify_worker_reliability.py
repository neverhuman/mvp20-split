"""LR-01 fixed three-trial managed-worker diagnostic; no retry-until-green."""

import argparse
import json
from datetime import datetime
from pathlib import Path

from verify_managed_numeric_campaign import verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'output', 'bundle-directory', 'materials', 'source-manifest'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    output, bundle = args.output.absolute(), args.bundle_directory.absolute()
    output.mkdir(parents=True, exist_ok=False)
    bundle.mkdir(parents=True, exist_ok=False)
    evidence = {'started_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'planned_trials': 3, 'execution_seconds_per_trial': 600, 'provider_calls': 0,
        'status': 'running', 'trials': [],
        'limits': ['Diagnostic baseline, not causal repair or soak evidence',
                   'Existing exact managed worker path; every failed history retained']}
    def save():
        (output / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    save()
    for number in range(1, 4):
        target = output / f'trial-{number}'
        print(f'LR-01 managed trial {number}/3', flush=True)
        try:
            verify(target, bundle / f'trial-{number}', args.materials.absolute(), args.source_manifest.absolute(),
                   root=args.root.absolute())
            result = json.loads((target / 'evidence.json').read_bytes())
            row = {'trial': number, 'status': 'passed', 'run_id': result['run_id'],
                'execution_seconds': result['execution_seconds'], 'drained': True,
                'status_scope': 'campaign execution, not fault-free worker lifecycle',
                'worker_faults_at_completion': {name: item['exit_code'] for name, item in
                    result['completed_controller']['scientific_workers'].items() if item['faulted']}}
        except Exception as error:
            failure_path = target / 'failure.json'
            failure = json.loads(failure_path.read_bytes()) if failure_path.exists() else {}
            owners = failure.get('cleanup', {}).get('owners', {})
            drained = bool(owners) and all(item['state'] == 'exited' and item['exit_code'] == 0
                                         for item in owners.values())
            row = {'trial': number, 'status': 'failed', 'error_type': type(error).__name__,
                   'run_id': failure.get('run_id'), 'drained': drained}
        evidence['trials'].append(row)
        save()
        print(json.dumps(row), flush=True)
        if not row['drained']:
            evidence['status'] = 'stopped_cleanup_unverified'
            save()
            raise SystemExit('Series stopped: owner drain not verified; inspect retained evidence')
    evidence['status'] = 'observed'
    evidence['finished_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    evidence['passed'] = sum(row['status'] == 'passed' for row in evidence['trials'])
    evidence['failed'] = 3 - evidence['passed']
    save()
    print('Fixed diagnostic series complete; evidence ' + str(output / 'evidence.json'), flush=True)


if __name__ == '__main__':
    main()
