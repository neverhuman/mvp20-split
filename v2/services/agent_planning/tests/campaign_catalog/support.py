"""300 independently identified descriptors behind a bounded test-owned HTTP catalog."""

import hashlib
import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from amphora_agent_planning.metadata_reads import MetadataTransport
from amphora_agent_planning.registry_access import RegistryReader
from amphora_contracts_tools import ReleasePage, ReleaseSnapshot

from ..registry_access.test_discovery import record


def catalog():
    target = record()
    values = [target]
    for index in range(299):
        value = target.model_dump(mode='json')
        binding = value['descriptor']['tool']['binding']
        binding['capability_id'] = f'synthetic.catalog-{index:03d}'
        value['lock']['tool'] = dict(binding)
        canonical = json.dumps({'profile': 'amphora-tool-release-v1', 'descriptor': value['descriptor']},
                               sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()
        value['lock']['descriptor_sha256'] = hashlib.sha256(canonical).hexdigest()
        values.append(ReleaseSnapshot.model_validate_json(json.dumps(value)))
    return target, tuple(sorted(values, key=lambda row: row.lock.descriptor_sha256))


@contextmanager
def hosted(records):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            path = urlsplit(self.path)
            self.server.calls.append(self.path)
            if self.headers.get('Authorization') != 'Bearer ' + 't' * 32:
                self.send_error(403)
                return
            if path.path == '/v1/releases':
                query = parse_qs(path.query)
                assert set(query) <= {'limit', 'after'} and query['limit'] == ['100']
                after = query.get('after', [''])[0]
                available = [row for row in records if row.lock.descriptor_sha256 > after]
                items = tuple(available[:100])
                value = ReleasePage(items=items, next_after=items[-1].lock.descriptor_sha256 if len(available) > 100 else None)
            else:
                matches = [row for row in records if path.path == '/v1/releases/' + row.lock.descriptor_sha256]
                if len(matches) != 1:
                    self.send_error(404)
                    return
                value = matches[0]
            raw = value.model_dump_json().encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.calls, server.daemon_threads = [], True
    thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
    thread.start()
    reader = RegistryReader(MetadataTransport('registry', f'http://127.0.0.1:{server.server_port}', 't' * 32))
    try:
        yield reader, server.calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join(2)
        assert not thread.is_alive()
