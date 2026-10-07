"""Sequential cold owner readback/browser smoke through independently installed Deployment."""

import argparse
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path


def verify(args):
    output = args.output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    scripts = Path(__file__).absolute().parent
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    environment['PYTHONUTF8'] = '1'

    def run(arguments):
        result = subprocess.run([str(args.python.absolute()), '-I', *arguments],
            cwd=scripts.parent.parent, env=environment, capture_output=True,
            timeout=300, creationflags=subprocess.CREATE_NO_WINDOW)
        with (output / 'smoke.log').open('ab') as stream:
            stream.write(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError('acceptance_smoke_failed')
        return result.stdout

    run(['-c', 'import pathlib,sys,amphora_deployment; '
         'assert pathlib.Path(amphora_deployment.__file__).is_relative_to(pathlib.Path(sys.prefix))'])
    checked = json.loads(run(['-m', 'amphora_deployment.acceptance', '--ledger', str(args.ledger.absolute()),
                             '--evidence-directory', str(args.evidence_directory.absolute())]))
    records = {}
    for name, script, options in (
        ('original', 'inspect_local_integrated.py', {
            'configuration': args.configuration, 'retained': args.retained}),
        ('browser', 'verify_local_browser.py', {
            'configuration': args.configuration, 'retained': args.retained,
            'public': args.public, 'successor': args.successor}),
        ('blocked', 'inspect_local_failure.py', {
            'configuration': args.failure_configuration, 'retained': args.failure_retained}),
    ):
        options.update(root=args.root, output=output / name)
        path = scripts / script
        arguments = [str(path)]
        for key, value in options.items():
            arguments.extend(['--' + key.replace('_', '-'), str(value.absolute())])
        launch = ('import runpy,sys; sys.path.insert(0,' + repr(str(scripts)) + '); '
                  'sys.argv=' + repr(arguments) + '; runpy.run_path(' + repr(str(path)) + ',run_name="__main__")')
        run(['-c', launch])
        evidence = json.loads((output / name / 'evidence.json').read_bytes())
        expected = 'passed' if name == 'browser' else 'readback_passed'
        if evidence['status'] != expected or evidence.get('provider_calls', evidence.get('additional_model_calls')) != 0:
            raise RuntimeError('acceptance_smoke_oracle_failed')
        records[name] = {'status': evidence['status'], 'run_id': evidence['run_id'],
                         'evidence': str((output / name / 'evidence.json').absolute())}
        print(name + ' installed-owner smoke passed', flush=True)
    report = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
              'status': 'passed', 'ledger': checked, 'scenarios': records,
              'provider_calls': 0, 'workers_started': False,
              'limits': ['Cold owner processes against already running restored stores; no new store recovery',
                         'Same selected host/user and retained owner installations/assets required']}
    (output / 'evidence.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('python', 'ledger', 'evidence-directory', 'root', 'configuration', 'retained',
                 'public', 'successor', 'failure-configuration', 'failure-retained', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    try:
        verify(parser.parse_args())
    except Exception:
        raise SystemExit('Acceptance smoke failed; retain its scoped output for diagnosis.') from None
