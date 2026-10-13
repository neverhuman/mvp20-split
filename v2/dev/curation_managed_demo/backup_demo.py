"""Current scientific demo cold cut, with exact readback/configuration identities."""
import argparse
import hashlib
from pathlib import Path

from campaign_curation_fixture.recovery import read
from capture_local_backup import capture, SCHEMAS
from local_backup_io import copy_tree
from local_numeric_configuration import write


class CurrentDemoCut:
    def __init__(self, inventory, serving):
        self.inventory, self.serving = inventory, serving
        self.record = read(inventory / 'inventory-evidence.json')
        assert self.record['status'] == 'passed' and self.record['all_owned_processes_drained']
        assert Path(self.record['source']) == serving
        raw = (inventory / 'readbacks.json').read_bytes()
        assert hashlib.sha256(raw).hexdigest() == self.record['readbacks_sha256']
        self.readbacks = read(inventory / 'readbacks.json')
        assert set(self.readbacks['runs']) == set(self.record['run_ids'])
        assert all(row['status'] == 'completed' for row in self.readbacks['runs'].values())
        assert read(inventory / 'drain.json')['status'] == 'drained'

    def owner_schemas(self, root, owners):
        assert root == Path(self.record['root'])
        assert set(owners) == set(SCHEMAS)
        original = read(self.serving / 'owners.json')['owners']
        for name, row in original.items():
            evidence = self.record['owners'][name]
            assert hashlib.sha256(Path(row['configuration']).read_bytes()).hexdigest() == evidence['configuration_sha256']
            assert hashlib.sha256((Path(row['installation']) / 'manifest.json').read_bytes()).hexdigest() == evidence['manifest_sha256']
            if name in owners:
                assert owners[name]['installation'] == row['installation']
        # Exact installed predecessor reviewed for UI-01.08j; no inference from stale
        # Deployment initial-migration receipts. Restore/migration still needs proof.
        assert self.record['owners']['planning']['packages']['amphora-agent-planning'] == '0.107.0'
        return SCHEMAS | {'planning': '0021'}

    def readback_evidence(self):
        return [{'sha256': self.record['readbacks_sha256'], 'run_id': identity,
                 'timestamp_local': self.record['timestamp_local']} for identity in self.record['run_ids']]

    def copy_installation(self, target):
        copy_tree(self.serving, target / 'serving-original')
        copy_tree(self.inventory, target / 'pre-migration-readbacks')

    def prepare(self, output):
        output.mkdir(parents=True, exist_ok=False)
        owners = read(self.serving / 'owners.json')
        owners['owners'].pop('gateway')
        for name, row in owners['owners'].items():
            source = Path(row['configuration'])
            def relocate(value):
                if isinstance(value, dict):
                    return {key: relocate(item) for key,item in value.items()}
                if isinstance(value, list):
                    return [relocate(item) for item in value]
                if isinstance(value, str) and value.endswith('.json') and not Path(value).is_absolute():
                    path = (source.parent / value).absolute()
                    assert '..' not in Path(value).parts and path.is_file()
                    return str(path)
                return value
            row['configuration'] = str(write(output / (name + '.json'), relocate(read(source))))
        write(output / 'owners.json', owners)
        return Path(read(Path(owners['owners']['artifact']['configuration']))['storage_root'])


def run(inventory, serving, output, evidence):
    basis = CurrentDemoCut(inventory, serving)
    config = evidence.parent / (evidence.stem + '-configuration')
    artifacts = basis.prepare(config)
    root = Path(basis.record['root'])
    result = capture(root, artifacts, config, output, [], basis=basis)
    write(evidence, result)
    print('Current demo cold backup verified; exact original stores restarted, no owners/provider', flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('inventory','serving','output','evidence'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    run(*(getattr(args,name).absolute() for name in ('inventory','serving','output','evidence')))
