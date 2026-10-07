"""Build four isolated current owners without starting services or changing stores."""

import argparse
import json
from datetime import datetime
from pathlib import Path

from install_owner_peer import install


OWNERS = {
    'artifact': ('amphora-data-artifacts', 'amphora_data_artifacts'),
    'research': ('amphora-research', 'amphora_research'),
    'planning': ('amphora-agent-planning', 'amphora_agent_planning'),
    'runtime': ('amphora-campaign-runtime', 'amphora_campaign_runtime'),
}


def prepare(output: Path):
    output = output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    owners = {}
    for name, (package, module) in OWNERS.items():
        python = install(output / name, package, [other for _, other in OWNERS.values() if other != module])
        record = json.loads((output / name / 'manifest.json').read_bytes())
        owners[name] = {'python': str(python), 'version': record['packages'][package],
                        'manifest': str(output / name / 'manifest.json')}
    (output / 'manifest.json').write_text(json.dumps({
        'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'installed_only', 'owners': owners,
        'limits': ['No services started', 'No stores changed', 'No provider calls',
                   'Actual-owner journey and independent Studio replacement remain pending'],
    }, indent=2) + '\n', encoding='utf-8')
    print('Four isolated current owners installed; acceptance remains pending', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    prepare(parser.parse_args().output)
