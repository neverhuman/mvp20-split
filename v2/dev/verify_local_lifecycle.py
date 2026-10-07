"""Actual installed owner failure/control/restart proof; no migrations or model calls."""

from datetime import datetime
import json
import os
from pathlib import Path
import secrets
import threading
import urllib.request

from amphora_deployment.installation import OwnerInstallation
from amphora_deployment.lifecycle import LifecycleEvents
from amphora_deployment.lifecycle.control import ControlServer
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.lifecycle.supervisor import OwnerBinding, Supervisor


def verify():
    root = Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation'
    routes = Routes.ensure(root)
    assert Routes.ensure(root) == routes
    directory = Path('.test-results/local-owner-inventory-20261006a/owners/registry').absolute()
    installation = OwnerInstallation.from_directory('registry', directory, Path('v2/services/capability_registry/uv.lock'))
    output = Path('.test-results/local-lifecycle-20261006a').absolute()
    output.mkdir(parents=True, exist_ok=False)
    absent = output / 'deliberately-absent-config.json'
    supervisor = Supervisor({'registry': OwnerBinding(installation, directory, absent, routes.port('registry'), {})},
                            LifecycleEvents(output / 'logs'))
    token = secrets.token_urlsafe(36)
    server = ControlServer(routes.port('supervisor'), supervisor, token)
    thread = threading.Thread(target=server.serve)
    thread.start()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def request(path, method='GET'):
        req = urllib.request.Request(routes.endpoint('supervisor') + path, method=method,
                                     headers={'Authorization':'Bearer '+token})
        with opener.open(req, timeout=15) as response:
            assert response.status == 200
            return json.loads(response.read())
    try:
        first = request('/owners/registry/start', 'POST')
        original = supervisor.processes['registry']
        assert original.process.wait(timeout=15) == 2
        repeated = request('/owners/registry/start', 'POST')
        assert repeated['pid'] == first['pid'] and repeated['state'] == 'exited'
        assert repeated['readiness'] == 'not_assessed'
        request('/owners/registry/restart', 'POST')
        replacement = supervisor.processes['registry']
        assert replacement is not original
        assert replacement.process.wait(timeout=15) == 2
        status = request('/status')
        request('/shutdown', 'POST')
    finally:
        server.stopping = True
        thread.join(timeout=5)
        for process in supervisor.processes.values():
            process.force_stop()
        assert not thread.is_alive()
    result = {'checked_at':datetime.now().astimezone().isoformat(timespec='seconds'),
              'routes':routes.to_record(), 'installed_registry_release':installation.release,
              'manifest_sha256':installation.installation_manifest_sha256,
              'repeat_start_did_not_retry':True, 'explicit_restart_used_fresh_process':True,
              'observed':status, 'control_shutdown_completed':True,
              'limits':['Missing configuration is intentional; this proves process failure handling, not application readiness.',
                        'No owner migrations, provider calls or scientific tool activation.',
                        'Credential was ephemeral for this bounded proof; persistent supervisor wiring remains.']}
    (output / 'evidence.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Installed Registry lifecycle/control failure proof passed:',output / 'evidence.json')


if __name__ == '__main__':
    try:
        verify()
    except Exception:
        raise SystemExit('Lifecycle verification failed; raw diagnostics suppressed.') from None
