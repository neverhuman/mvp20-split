"""Installed Planning exact historical replays; no credentials, SQL or provider calls."""
import json
import runpy
import sys
from pathlib import Path
from amphora_agent_planning.curation_input import CurationEnvelope
from amphora_agent_planning.curation_output import CurationOutput


def main(root, output):
    output.mkdir(parents=True, exist_ok=False)
    original = runpy.run_path(str(Path(__file__).with_name('material_scientific.py')))
    original['main'](root, output / 'sixteen-originals.json')
    prior = json.loads((output / 'sixteen-originals.json').read_bytes())
    records = list(prior['replays'])
    for suffix in ('c', 'd', 'e', 'f', 'g'):
        path = root / ('curation-demo-live-browser-20261012' + suffix)
        raw = (path / 'original-packet.json').read_bytes()
        request = original['request'](json.loads(raw))
        envelope = CurationEnvelope.bind(request, raw)
        assert envelope.body == (path / 'original-envelope.json').read_bytes()
        # These are schema-valid abstentions/proposals. Compiler acceptance is
        # separately retained and must not be inferred from output parsing.
        CurationOutput.parse((path / 'original-output.json').read_bytes(), request)
        records.append({'path': str(path), 'envelope_sha256': envelope.sha256,
                        'acceptance_unchanged': True})
    assert len(records) == 21
    (output / 'evidence.json').write_text(json.dumps({'status': 'passed',
        'provider_calls': 0, 'replays': records, 'scope': 'exact envelope and output parser replay; not compiler acceptance'}, indent=2))
    print('Twenty-one original envelopes and parser outcomes preserved')


if __name__ == '__main__':
    main(*map(Path, sys.argv[1:]))
