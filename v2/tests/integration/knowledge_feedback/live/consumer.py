"""Public Node consumers; owner credentials are stdin-only and never retained."""
import json
import subprocess

from .process import base_environment


def verify(scenario, records, studio, output, *, browser):
    owners = {name: {'endpoint': owner.endpoint, 'token': owner.token} for name, owner in
        [('data', scenario.data), ('research', scenario.research), ('knowledge', scenario.knowledge)]}
    def run(script, payload, timeout):
        process = subprocess.run(['node', script], cwd=studio, input=json.dumps(payload), env=base_environment(),
            capture_output=True, text=True, encoding='utf-8', timeout=timeout,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        assert process.returncode == 0, 'Actual Studio consumer failed: ' + process.stderr[-2000:]
        return json.loads(process.stdout)
    result = {'studio': run('scripts/probe-scientific.mjs', {'owners': owners, 'records': records}, 45)}
    if browser:
        owners = {name: {'endpoint': owner.endpoint, 'token': scenario.environments[key]['BROWSER_TOKEN']}
            for name, key, owner in [('data', 'data_artifacts', scenario.data),
                ('research', 'research', scenario.research), ('knowledge', 'knowledge', scenario.knowledge)]}
        result['browser'] = run('tests/integration/explore_live.mjs',
            {'owners': owners, 'records': records, 'output': str(output)}, 120)
    return result
