"""One reviewed follow-up within the approved additive budget; no provider enabled."""
import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from amphora_contracts_campaign_curation import CurationSpecification
from amphora_deployment.credentials import CredentialVault
from amphora_deployment.persistence.state import LocalState
from campaign_curation_fixture.recovery import read
from .configuration import freeze, planning_python, worker_environment
from .run import owned_process


def prepare(root, serving, previous, direction, output):
    output.mkdir(parents=True, exist_ok=False)
    for name, digest in read(previous / 'frozen-files.json').items():
        assert hashlib.sha256((previous / name).read_bytes()).hexdigest() == digest
    view = read(previous / 'supported/current-view.json')
    assert view['receipt']['phase'] in {'abstained', 'failed'} and view['validated_draft'] is None
    feedback = read(direction)
    assert feedback['source_curation'] == view['receipt']['reference']
    assert feedback['original_output_sha256'] == hashlib.sha256((previous / 'supported/original-output.json').read_bytes()).hexdigest()
    command = read(previous / 'supported/curation-command.json')
    CurationSpecification.model_validate_json(json.dumps(dict(command['payload'], direction=feedback['proposed_direction'])))
    state = LocalState.snapshot(root)
    vault = CredentialVault(root / 'credentials.dpapi', state['deployment_id']).load()
    names = ('artifact', 'runtime', 'registry', 'knowledge', 'research')
    refs = vault.environment([name.upper() + '_OPERATOR_TOKEN' for name in names])
    api = SimpleNamespace(tokens={name: refs[name.upper() + '_OPERATOR_TOKEN'] for name in names})
    environment = worker_environment(root, api)
    python = planning_python(serving)
    assert owned_process([python, '-I', Path(__file__).with_name('replay_extra.py'), previous / 'supported', output / 'prior-replay.json'], environment, output / 'preparation.log', timeout=60) == 0
    for name in ('roots.json', 'curation-policy.json', 'curation-worker.json', 'planning-material.json'):
        freeze(output / name, read(previous / name))
    assert owned_process([python, '-I', Path(__file__).with_name('allowance.py'), output / 'curation-worker.json', output / 'initial-allowance.json'], environment, output / 'preparation.log', timeout=60) == 0
    allowance = read(output / 'initial-allowance.json')
    prior = read(previous / 'live-allowance.json')['initial']
    assert allowance['authorization'] == 'UI-01.08i' and allowance['maximum_slots'] == 53 and allowance['maximum_units'] == 13300000000
    assert allowance['reserved_slots'] == prior['reserved_slots'] + 1
    assert allowance['reserved_units'] == prior['reserved_units'] + 250000000
    assert allowance['remaining_slots'] > 0 and allowance['remaining_reservation_units'] >= 250000000
    declaration = dict(read(previous / 'scope-declaration.json'), previous_declaration_sha256=hashlib.sha256((previous / 'scope-declaration.json').read_bytes()).hexdigest(), qualification='UI-01.08i-followup-' + str(allowance['reserved_slots'] + 1))
    freeze(output / 'scope-declaration.json', declaration)
    repair = read(previous / 'repair-evidence.json')
    repair['offline']['original_replays'] += 1
    repair['prior_original'] = read(output / 'prior-replay.json')
    repair['feedback_source'] = view['receipt']['reference']
    freeze(output / 'repair-evidence.json', repair)
    freeze(output / 'feedback-direction.json', feedback)
    freeze(output / 'live-allowance.json', {'scope': allowance['scope'], 'diagnostic_stage': 7, 'maximum_new_physical_calls': 1, 'maximum_new_original_units': 250000000, 'initial': allowance, 'repair': repair})
    names = ('scope-declaration.json', 'roots.json', 'curation-policy.json', 'curation-worker.json', 'initial-allowance.json', 'live-allowance.json', 'planning-material.json', 'repair-evidence.json', 'feedback-direction.json', 'prior-replay.json')
    freeze(output / 'frozen-files.json', {name: hashlib.sha256((output / name).read_bytes()).hexdigest() for name in names})
    print('Follow-up frozen; exact prior replay and actual owner allowance verified; no provider enabled', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'serving', 'previous', 'direction', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    prepare(*(getattr(args, name).absolute() for name in ('root', 'serving', 'previous', 'direction', 'output')))
