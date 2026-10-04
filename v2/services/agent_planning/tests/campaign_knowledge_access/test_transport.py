import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from amphora_agent_planning.campaign_knowledge_access import CampaignKnowledgeReader
from amphora_agent_planning.knowledge_access import KnowledgeTransport

from .test_reader import selected


def test_full_campaign_read_uses_only_authenticated_exact_public_routes():
    selection, peer = selected()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            self.server.calls.append((self.path, self.headers.get('Authorization'), payload))
            raw = peer.records[self.path].model_dump_json().encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads, server.calls = True, []
    thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
    thread.start()
    try:
        reader = CampaignKnowledgeReader(KnowledgeTransport(f'http://127.0.0.1:{server.server_port}', 't' * 32))
        result = reader.read(selection)
        assert result.failure is None and result.calls == 3 and result.bytes > 0
        pins = selection.parts()[0]
        assert server.calls == [(path, 'Bearer ' + 't' * 32, ref.model_dump(mode='json')) for path, ref in (
            ('/v1/graph-profiles/read', pins.graph), ('/v1/graph-snapshots/read', pins.base.snapshot),
            ('/v1/graph-changes/read', pins.base.change))]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(2)
