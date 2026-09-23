"""Verify the frozen tracked v1 snapshot without modifying it."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((Path(__file__).with_name('v1-baseline.sha256.json')).read_text(encoding='utf-8'))
    failures = []
    for relative, expected in manifest['files'].items():
        path = root / relative
        if not path.is_file():
            failures.append(f'MISSING {relative}')
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            failures.append(f'CHANGED {relative}')
    result = subprocess.run(
        ['git', '-c', f'safe.directory={root.as_posix()}', '-C', str(root), 'ls-files', '-z', '--', 'v1/'],
        capture_output=True, check=True,
    )
    tracked = set(result.stdout.decode('utf-8').strip('\0').split('\0')) - {''}
    # Relocation metadata is separate from the preserved implementation snapshot.
    maintenance_files = {'v1/tools/verify_v1_baseline.py', 'v1/tools/v1-baseline.sha256.json', 'v1/REPOSITORY_LAYOUT.md'}
    failures.extend(f'ADDED {p}' for p in sorted(tracked - manifest['files'].keys() - maintenance_files))
    if failures:
        print('\n'.join(failures))
        return 1
    print(f"Verified {len(manifest['files'])} frozen v1 files; no baseline content changes.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
