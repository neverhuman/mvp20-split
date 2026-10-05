"""Fresh campaign closure plus replacement byte vectors and exact production reuse."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from verify_planning_context import ROOT, verify


def payload(directory):
    wheel = next((directory / 'wheels').glob('amphora_agent_planning-*.whl'))
    with zipfile.ZipFile(wheel) as archive:
        return {name: hashlib.sha256(archive.read(name)).hexdigest() for name in archive.namelist()
                if name.startswith('amphora_agent_planning/') and not name.endswith('/README.md')}


def closeout(output, predecessor):
    output, predecessor = output.absolute(), predecessor.absolute()
    assert json.loads((predecessor / 'manifest.json').read_bytes())['status'] == 'passed'
    output.mkdir(parents=True, exist_ok=False)
    initial = output / 'initial'
    verify(initial, 'campaign_closeout')
    initial_manifest = json.loads((initial / 'manifest.json').read_bytes())
    production = payload(initial)
    assert production == payload(predecessor), 'Reused current owner evidence requires exact implementation payloads'
    env = {key: value for key, value in os.environ.items() if not key.startswith('AMPHORA') and key != 'PYTHONPATH'}
    env['PYTHONUTF8'] = '1'
    uv = ROOT / '.venv/Scripts/uv.exe'
    replacement = output / 'replacement'

    def run(arguments, timeout=120):
        result = subprocess.run([str(item) for item in arguments], cwd=output, env=env,
            capture_output=True, text=True, encoding='utf-8', timeout=timeout)
        with (output / 'replacement.log').open('a', encoding='utf-8') as stream:
            stream.write(result.stdout + result.stderr)
        assert result.returncode == 0, 'Replacement acceptance failed; inspect retained replacement.log'

    run([uv, 'venv', '--python', sys.executable, replacement])
    python = replacement / 'Scripts/python.exe'
    run([uv, 'pip', 'install', '--python', python, *sorted((initial / 'wheels').glob('*.whl')), 'pytest>=8,<9', 'jsonschema>=4,<5'])
    run([python, '-I', '-c', "import importlib.util,sys; from pathlib import Path; import amphora_agent_planning; "
        "assert Path(amphora_agent_planning.__file__).absolute().is_relative_to(Path(sys.prefix).absolute()); "
        "assert all(importlib.util.find_spec(n) is None for n in "
        "('amphora_campaign_runtime','amphora_research','amphora_knowledge','amphora_data_artifacts','amphora_capability_registry','fastapi'))"])
    areas = ['campaign_packet/test_replay.py', 'campaign_output/test_predecessor.py',
             'campaign_decisions/test_publication_profile.py', 'graph_context/test_compatibility.py',
             'providers/test_task_output.py']
    suites = []
    for index, area in enumerate(areas):
        report = output / f'replacement-{index}.xml'
        run([python, '-I', '-m', 'pytest', initial / 'tests/service' / area, '--import-mode=importlib',
             '--tb=short', '-q', '--junitxml=' + str(report)])
        suites.extend(ET.parse(report).getroot().findall('testsuite'))
        print(json.dumps({'replacement_area': area}), flush=True)
    count = sum(int(s.attrib['tests']) for s in suites)
    assert count > 0 and all(int(s.attrib[key]) == 0 for s in suites for key in ('errors', 'failures', 'skipped'))
    manifest = {'verified_at': datetime.now(ZoneInfo('America/Chicago')).strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'passed', 'planning': initial_manifest['planning'], 'contracts': initial_manifest['contracts'],
        'installations': 2, 'initial': initial_manifest,
        'replacement': {'tests': count, 'seconds': sum(float(s.attrib['time']) for s in suites), 'areas': areas},
        'production_payload_sha256': production, 'equal_predecessor_manifest': str(predecessor / 'manifest.json'),
        'limits': ['Campaign-owned pure/transport boundaries and exact predecessor replacement vectors',
            'SQL/actual-owner/crash/source-rights proofs reused only against exact unchanged current production payloads',
            'No migrations, resets, private peer dependencies, live provider or scientific efficacy claim']}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'passed', 'initial_tests': initial_manifest['tests'], 'replacement_tests': count}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--predecessor', type=Path, required=True)
    args = parser.parse_args()
    closeout(args.output, args.predecessor)
