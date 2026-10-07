"""Actual owned supervisor/API/TLS death and original Linux-turn reconciliation."""

import json
import socket
import time
from urllib.parse import urlparse

from amphora_deployment.profile import ProfileError
from amphora_deployment.scientific_workers.engine import ContainerEngine
from amphora_deployment.scientific_workers.journal import ContainerJournal
from amphora_deployment.scientific_workers.ownership import journal_path, require_released
from amphora_deployment.scientific_workers.profiles import ToolProfile

from local_demo_controller import Controller
from local_numeric_configuration import write


def interrupt_and_resume(controller, campaign, root, configuration, label, prepared, deployment_id, output):
    """One predeclared fault; zero provider keys, no daemon disruption or new admission."""
    manifests = json.loads((configuration / (label + '-scientific.json')).read_bytes())
    entry = manifests['workers']['evolution-seed']
    profile = ToolProfile.pin('evolution-seed', entry['image_id'], entry['configuration'], entry['certificate'],
                              prepared['ports']['runtime'], prepared['ports']['artifact'])
    journal = ContainerJournal(journal_path(root, profile), deployment_id, profile.name, profile.fingerprint)
    engine = ContainerEngine()
    controller.control('/scientific-workers/evolution-seed/start', 'POST')
    deadline = time.monotonic() + 30
    while True:
        original = journal.read()
        if original is not None and original['phase'] == 'started':
            controller.control('/scientific-workers/evolution-seed/quiesce', 'POST')
            observed = engine.observe(original, profile)
            if observed is not None and observed.status == 'running':
                break
        assert time.monotonic() < deadline, 'Live container fault barrier missed; do not claim interruption'
        time.sleep(.02)
    before = controller.control('/status')
    assert before['scientific_workers']['evolution-seed']['active_turn']
    write(output / 'interruption-barrier.json', {'turn': original, 'controller': before,
        'run_id': campaign.run_id, 'limits': 'Running Linux process; accepted scientific invocation is not assumed'})
    started = time.monotonic()
    controller.close()  # Exact Windows job: supervisor, native workers, owner APIs and TLS.
    unavailable = []
    endpoints = []
    for name in ('supervisor', 'runtime', 'artifact', 'research', 'knowledge', 'planning', 'registry'):
        address = urlparse(controller.routes.endpoint(name))
        endpoints.append((name, address.hostname, address.port))
    endpoints += [('tls-' + name, '127.0.0.1', port) for name, port in prepared['ports'].items()]
    stop_deadline = time.monotonic() + 10
    for name, host, port in endpoints:
        while True:
            with socket.socket() as connection:
                connection.settimeout(.25)
                stopped = connection.connect_ex((host, port)) != 0
            if stopped:
                unavailable.append(name)
                break
            assert time.monotonic() < stop_deadline, 'Owned listener survived bounded job shutdown'
            time.sleep(.05)
    retained = journal.read()
    assert retained['turn_id'] == original['turn_id'] and retained['container_id'] == original['container_id']
    try:
        require_released(root, deployment_id)
        raise AssertionError('Unresolved container did not block migrations')
    except ProfileError as error:
        assert str(error) == 'migration_requires_reconciled_containers'
    replacement = Controller(root, configuration, controller.routes, label,
                             model_key='dry-preflight-no-provider-credential')
    try:
        campaign.controller = replacement
        replacement.start_owners(campaign.tokens['REGISTRY_OPERATOR_TOKEN'])
        latencies = []
        def reconciled():
            tick = time.monotonic()
            state = replacement.control('/status')['scientific_workers']['evolution-seed']
            latencies.append(time.monotonic() - tick)
            assert latencies[-1] < .5
            return not state['active_turn']
        replacement.wait(reconciled, timeout=90)
        final = journal.read()
        assert final['phase'] == 'released'
        for key in ('turn_id', 'container_id', 'sequence', 'binding_sha256'):
            assert final[key] == original[key], 'Recovery replaced an original tool turn'
        assert engine.observe(final, profile) is None
        assert campaign.call('runtime', campaign.admission_path, campaign.admission_command) == campaign.admission
        status = replacement.control('/status')['scientific_workers']['evolution-seed']
        if status['faulted']:
            replacement.control('/scientific-workers/evolution-seed/recover', 'POST')
        for name in ('runtime-deliver', 'runtime-checkpoint', 'runtime-coordinate'):
            replacement.control('/workers/' + name + '/start', 'POST')
        elapsed = time.monotonic() - started
        assert elapsed < 180, 'Owner/turn recovery exceeded180second bound'
        write(output / 'interruption-recovery.json', {'status': 'passed', 'original': original, 'retained': retained,
            'final': final, 'unavailable_owners': unavailable, 'tls_unavailable': True,
            'migration_blocked': True, 'exact_admission_replay': True, 'same_turn_no_restart': True,
            'elapsed_seconds': elapsed, 'maximum_control_latency_seconds': max(latencies),
            'provider_calls': 0, 'limits': ['Actual job death and Docker turn adoption; shared daemon remains running',
                'Live process barrier does not establish a scientific invocation had already been accepted']})
        return replacement
    except BaseException:
        replacement.close()
        raise
