import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from types import SimpleNamespace
from urllib.request import build_opener, ProxyHandler

import pytest
from curation_managed_demo.serving_copy import copy_serving
from curation_managed_demo.static_identity import verify_static


def write(path, value):
    path.write_text(json.dumps(value), encoding='utf-8')


def copies(tmp_path):
    base = tmp_path / '.test-results'
    old, source, target = (base / ('curation-demo-serving-' + name) for name in ('a', 'd', 'e'))
    for path in (old, source):
        (path / 'public').mkdir(parents=True)
        (path / 'schema.json').write_bytes(b'{ "immutable": true }\n')
        write(path / 'gateway.json', {'public_directory': str(old / 'public')})
    write(source / 'owners.json', {'owners': {'gateway': {'configuration': str(old / 'gateway.json'),
                                                        'installation': str(tmp_path / 'external-owner')}}})
    write(source / 'artifact.json', {'profiles': [{'schema_path': str(old / 'schema.json')}]})
    return old, source, target


def test_ancestor_references_rebase_but_external_installation_and_schema_bytes_do_not(tmp_path):
    old, source, target = copies(tmp_path)
    original = (source / 'owners.json').read_bytes()
    changes = copy_serving(source, target)
    owner = json.loads((target / 'owners.json').read_bytes())['owners']['gateway']
    assert Path(owner['configuration']) == target.resolve() / 'gateway.json'
    assert owner['installation'] == str(tmp_path / 'external-owner')
    assert Path(json.loads((target / 'gateway.json').read_bytes())['public_directory']) == target.resolve() / 'public'
    assert (target / 'schema.json').read_bytes() == (old / 'schema.json').read_bytes()
    assert (source / 'owners.json').read_bytes() == original
    assert len(changes) == 3


@pytest.mark.parametrize('defect', ['missing', 'schema-drift'])
def test_invalid_reference_fails_before_creating_new_copy(tmp_path, defect):
    old, source, target = copies(tmp_path)
    if defect == 'missing':
        write(source / 'gateway.json', {'public_directory': str(old / 'absent')})
    else:
        (source / 'schema.json').write_bytes(b'{}')
    with pytest.raises(AssertionError):
        copy_serving(source, target)
    assert not target.exists()


@pytest.mark.parametrize('stale', [False, True])
def test_actual_http_asset_identity_rejects_stale_gateway(tmp_path, stale):
    serving = tmp_path / 'serving'
    (serving / 'public').mkdir(parents=True)
    write(serving / 'owners.json', {'owners': {'gateway': {'configuration': str(serving / 'gateway.json')}}})
    write(serving / 'gateway.json', {'public_directory': str(serving / 'public')})
    bodies = {'/': b'<html>current</html>', '/app.js': b'current javascript', '/app.css': b'current css'}
    for name, route in (('index.html', '/'), ('app.js', '/app.js'), ('app.css', '/app.css')):
        (serving / 'public' / name).write_bytes(bodies[route])
    if stale:
        bodies['/app.js'] = b'old javascript'

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(bodies[self.path])

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    api = SimpleNamespace(controller=SimpleNamespace(opener=build_opener(ProxyHandler({})),
        routes=SimpleNamespace(endpoint=lambda _name: 'http://127.0.0.1:' + str(server.server_port))))
    try:
        if stale:
            with pytest.raises(AssertionError, match='different asset: app.js'):
                verify_static(api, serving, tmp_path)
            assert not (tmp_path / 'static-assets.json').exists()
        else:
            result = verify_static(api, serving, tmp_path)
            assert result['status'] == 'passed' and len(result['files']) == 3
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
