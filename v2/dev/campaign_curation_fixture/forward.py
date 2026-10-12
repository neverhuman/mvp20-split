"""Forward only the isolated restored Planning store to the qualified release."""
import hashlib
import os
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.installation import OwnerInstallation
from amphora_deployment.persistence.migrations import require_stopped
from amphora_deployment.persistence.state import LocalState
from amphora_deployment.scientific_workers.ownership import require_released
from local_numeric_configuration import write


def migrate(root, installation, predecessor, output):
    identified = OwnerInstallation.from_directory('planning', installation,
        Path(__file__).resolve().parents[2] / 'services/agent_planning/uv.lock')
    assert identified.release == '0.127.0'
    record_path = output / 'planning-forward.json'
    assert not record_path.exists(), 'Inspect an existing migration receipt before retrying'
    prior = predecessor / 'environment/Lib/site-packages/amphora_agent_planning/persistence/migrations/versions'
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in prior.iterdir()
              if p.suffix in {'.py', '.sql'}}
    assert hashes
    wheel = next((installation / 'wheels').glob('amphora_agent_planning-0.127.0-*.whl'))
    with zipfile.ZipFile(wheel) as archive:
        for name, digest in hashes.items():
            assert hashlib.sha256(archive.read('amphora_agent_planning/persistence/migrations/versions/' + name)).hexdigest() == digest
    with LocalState(root) as state:
        assert state.record.get('restore', {}).get('backup_id') == '9fd2a863a42d48e0ac5bef3b14aff734'
        assert state.record['phase'] == 'stores_ready'
        require_stopped(state.record['routes'])
        require_released(root, state.identity)
        bundle = CredentialVault(root / 'credentials.dpapi', state.identity).load()
        password = bundle.environment(['PG_PLANNING_MIGRATOR_PASSWORD'])['PG_PLANNING_MIGRATOR_PASSWORD']
        pg = state.record['postgres']
        assert pg['host'] == '127.0.0.1'
        env = {k: v for k, v in os.environ.items() if k.upper() in {
            'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
        env.update(PYTHONUTF8='1', AMPHORA_PLANNING_MIGRATION_URL='postgresql+psycopg://planning_migrator:' +
            quote(password, safe='') + '@127.0.0.1:' + str(pg['port']) + '/amphora_local?connect_timeout=5')
        evidence = {'status': 'running', 'started_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'owner': 'planning', 'release': identified.release, 'initial_receipt_preserved': state.record['migrations'].get('planning'),
            'prior_migration_hashes': hashes, 'approval': 'UI-01.08 approved additive curation boundary; isolated qualification',
            'installation_manifest_sha256': identified.installation_manifest_sha256}
        write(record_path, evidence)
        result = subprocess.run([str(installation / 'environment/Scripts/python.exe'), '-I', '-m',
            'amphora_agent_planning.persistence.migrate'], env=env, capture_output=True, timeout=180,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        (output / 'planning-forward.log').write_bytes(result.stdout + result.stderr)
        evidence.update(status='passed' if result.returncode == 0 else 'failed', exit_code=result.returncode,
                        finished_local=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        write(record_path, evidence)
        assert result.returncode == 0, 'Planning migration failed; retain evidence for forward repair'
