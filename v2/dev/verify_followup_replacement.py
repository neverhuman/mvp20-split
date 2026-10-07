"""Two clean Studio consumers of identical retained follow-up owner records."""

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from campaign_context_fixture.support import environment
from verify_followup_browser import verify
from verify_studio import stage_source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('installation', 'records', 'source', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    node, npm = shutil.which('node'), shutil.which('npm.cmd' if os.name == 'nt' else 'npm')
    assert node and npm, 'Node and npm required'
    output = args.output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    pins = {}
    with tempfile.TemporaryDirectory(prefix='amphora-followup-replacement-') as directory:
        root = Path(directory).absolute()
        for label in ('original', 'replacement'):
            workspace = root / label
            workspace.mkdir()
            staged, sources, schemas = stage_source(workspace)
            for step, command in (
                ('install', [npm, 'ci', '--ignore-scripts', '--no-audit', '--no-fund']),
                ('verify', [node, 'scripts/verify.mjs']),
            ):
                result = subprocess.run(command, cwd=staged, env=environment(), capture_output=True,
                    text=True, encoding='utf-8', timeout=240,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                (output / f'{label}-{step}.log').write_text(result.stdout + result.stderr, encoding='utf-8')
                assert result.returncode == 0, f'{label} {step} failed; inspect bounded log'
            count = re.search(r'(?:tests|pass)\s+(\d+)', result.stdout)
            assert count, 'Node test count missing'
            pins[label] = {'source_sha256': sources, 'public_schema_pins': schemas, 'tests': int(count.group(1))}
            print(f'{label}: independent install and {count.group(1)} tests passed', flush=True)
            verify(args.installation, args.records, args.source, output / label, staged)
        assert pins['original'] == pins['replacement'], 'Replacement source/schema/test drift'
    evidence = {
        'verified_at': datetime.now(ZoneInfo('America/Chicago')).strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'passed', 'installations': pins,
        'scope': 'Two independent locked Studio installs; same retained actual-owner browser and artifact oracles',
        'limits': ['Reproducible consumer replacement, not an independently rewritten UI',
                   'No provider calls, owner migrations, active graph writes, or scientific improvement claim'],
    }
    (output / 'manifest.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print('Independent follow-up replacement passed: ' + str(output), flush=True)


if __name__ == '__main__':
    main()
