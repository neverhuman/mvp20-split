"""Real local protocol peers expose exact byte, authorization and deadline failures."""

import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import pytest
from amphora_campaign_runtime.supervision_capture import (
    CaptureReader,
    CaptureUnavailable,
)
from amphora_campaign_runtime.supervision_capture.reader import ReadWindow

from ..supervision_responses.support import response

TOKEN = 'synthetic-capture-reader-token-0000000000000'


@pytest.fixture
def peer():
    value, capture = response('abstain')
    state = SimpleNamespace(reference=value.capture, metadata=value.capture.model_dump_json().encode(),
                            content=capture, requests=[], status=200, slow=False, encoding='identity',
                            metadata_type='application/json')
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            state.requests.append((self.path, self.headers.get('Authorization')))
            metadata = not self.path.endswith('/processing-content')
            body = state.metadata if metadata else state.content
            status = 200 if metadata else state.status
            self.send_response(status)
            self.send_header('Content-Type', state.metadata_type if metadata else 'application/octet-stream')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Content-Encoding', state.encoding)
            self.send_header('Location', 'http://127.0.0.1:1/forbidden-redirect')
            self.end_headers()
            try:
                if state.slow:
                    for byte in body:
                        self.wfile.write(bytes([byte]))
                        self.wfile.flush()
                        time.sleep(.03)
                else:
                    self.wfile.write(body)
            except OSError:
                pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': .02}, daemon=True)
    thread.start()
    state.endpoint = f'http://127.0.0.1:{server.server_port}'
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_exact_capture_uses_processing_content_and_no_empty_diagnostic_fetch(peer):
    reader = CaptureReader(peer.endpoint, TOKEN)
    assert reader.fetch(None) is None and not peer.requests
    assert reader.fetch(peer.reference) == peer.content
    base = '/v1/artifacts/' + peer.reference.artifact_id
    assert peer.requests == [(base, 'Bearer ' + TOKEN), (base + '/processing-content', 'Bearer ' + TOKEN)]


@pytest.mark.parametrize('status,reason', [(401, 'processing_denied'), (403, 'processing_denied'),
                                        (404, 'capture_unavailable'), (302, 'peer_unavailable'), (503, 'peer_unavailable')])
def test_denied_missing_redirect_and_unavailable_never_retry(peer, status, reason):
    peer.status = status
    with pytest.raises(CaptureUnavailable, match=reason):
        CaptureReader(peer.endpoint, TOKEN).fetch(peer.reference)
    assert len(peer.requests) == 2


@pytest.mark.parametrize('mode,reason,calls', [
    ('metadata-identity', 'metadata_mismatch', 1), ('metadata-duplicate', 'metadata_invalid', 1),
    ('metadata-size', 'response_limit', 1), ('metadata-type', 'metadata_type', 1),
    ('encoding', 'capture_encoding', 1), ('body-size', 'response_limit', 2),
    ('body-hash', 'content_mismatch', 2), ('body-short', 'content_mismatch', 2),
])
def test_original_metadata_and_bytes_must_match(peer, mode, reason, calls):
    if mode == 'metadata-identity':
        peer.metadata = peer.reference.model_copy(update={'artifact_id': 'other'}).model_dump_json().encode()
    elif mode == 'metadata-duplicate':
        peer.metadata = b'{"artifact_id":"a","artifact_id":"b"}'
    elif mode == 'metadata-size':
        peer.metadata = b' ' * 262145
    elif mode == 'metadata-type':
        peer.metadata_type = 'text/html'
    elif mode == 'encoding':
        peer.encoding = 'gzip'
    elif mode == 'body-size':
        peer.content += b' '
    elif mode == 'body-hash':
        peer.content = b'x' * len(peer.content)
    elif mode == 'body-short':
        peer.content = peer.content[:-1]
    with pytest.raises(ValueError, match=reason):
        CaptureReader(peer.endpoint, TOKEN).fetch(peer.reference)
    assert len(peer.requests) == calls


def test_trickled_bytes_cannot_extend_whole_deadline(peer):
    peer.slow = True
    started = time.monotonic()
    with pytest.raises(CaptureUnavailable):
        CaptureReader(peer.endpoint, TOKEN, seconds=.15).fetch(peer.reference)
    assert time.monotonic() - started < 1.5 and len(peer.requests) == 1


@pytest.mark.parametrize('endpoint', ['http://example.com:80', 'https://127.0.0.1:80',
                                     'http://127.0.0.1:80/path', 'http://u:p@127.0.0.1:80',
                                     'http://127.0.0.1:bad', 'http://127.0.0.1:80?x=1'])
def test_caller_urls_are_not_allowed(endpoint):
    with pytest.raises(ValueError, match='capture_endpoint'):
        CaptureReader(endpoint, TOKEN)


def test_credentials_and_window_bounds(peer):
    with pytest.raises(ValueError, match='capture_credential'):
        CaptureReader(peer.endpoint, 'bad\r\ncredential')
    for seconds in [0, 11, True, float('nan')]:
        with pytest.raises(ValueError, match='deadline_configuration'):
            ReadWindow(seconds)
    window = ReadWindow(1)
    window.start()
    window.start()
    with pytest.raises(ValueError, match='call_limit'):
        window.start()
    with pytest.raises(ValueError, match='total_bytes'):
        window.consume(327681)
    with pytest.raises(ValueError, match='capture_size_limit'):
        CaptureReader(peer.endpoint, TOKEN).fetch(peer.reference.model_copy(update={'size_bytes': 65537}))
