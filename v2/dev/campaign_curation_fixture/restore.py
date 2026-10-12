"""Prepare separate stores from the trusted cold cut; never enable traffic."""
import argparse
from pathlib import Path

from local_numeric_configuration import write
from restore_local_backup import restore


EXPECTED_OWNERS = {
    'artifact': ('0.30.0', '0012'), 'knowledge': ('0.18.0', '0007'),
    'planning': ('0.102.0', '0020'), 'registry': ('0.1.0', '0001'),
    'research': ('0.40.0', '0016'), 'runtime': ('0.65.0', '0028'),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('backup', 'target', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    v2 = Path(__file__).resolve().parents[2]
    trusted = v2 / 'docs/Audits/Evidence/BP-09-Deployment/Cold_Backup.json'
    result = restore(args.backup.resolve(), trusted, args.target.resolve(),
                     args.output.resolve(), EXPECTED_OWNERS)
    write(args.output.resolve() / 'restore.json', result)
    print('Isolated curation stores restored; owner integration remains pending.', flush=True)


if __name__ == '__main__':
    main()
