"""Serving acceptance checks planned configuration and actual public asset bytes."""
import hashlib
import json
from datetime import datetime
from pathlib import Path


def verify_static(api, serving, output):
    serving = Path(serving).resolve()
    owners = json.loads((serving / 'owners.json').read_bytes())
    assert Path(owners['owners']['gateway']['configuration']).resolve() == serving / 'gateway.json'
    gateway = json.loads((serving / 'gateway.json').read_bytes())
    assert Path(gateway['public_directory']).resolve() == serving / 'public'
    files = {}
    for name, route in (('index.html', '/'), ('app.js', '/app.js'), ('app.css', '/app.css')):
        expected = (serving / 'public' / name).read_bytes()
        assert 0 < len(expected) <= 16777216, 'Static asset size'
        with api.controller.opener.open(api.controller.routes.endpoint('gateway') + route, timeout=20) as response:
            assert response.status == 200
            actual = response.read(len(expected) + 1)
        assert actual == expected, 'Gateway serves a different asset: ' + name
        files[name] = {'sha256': hashlib.sha256(actual).hexdigest(), 'bytes': len(actual)}
    record = {'status': 'passed', 'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
              'serving': str(serving), 'files': files, 'provider_calls': 0}
    (Path(output) / 'static-assets.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    return record
