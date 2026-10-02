import hashlib
import json
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from amphora_research.assessment.policy import AssessmentError
from amphora_research.assessment.reader import AssessmentDataReader, AssessmentPeerUnavailable, _decode

from .test_policy import METHOD, OTHER, SCOPE, artifact

TOKEN = "fixture-read-token-" * 3
CONTENT = b'{"fixture":true}'
REFERENCE = artifact("result", size_bytes=len(CONTENT), sha256=hashlib.sha256(CONTENT).hexdigest())
PATH = "/v1/artifacts/result"


def proof():
    return {"schema_version": "1", "origin": {"schema_version": "1",
            "command_family": "artifacts.begin_derived_upload", "command_id": "begin",
            "scope": SCOPE.model_dump(mode="json"), "actor_id": "publisher"},
            "request_sha256": "a" * 64, "upload_id": "upload", "artifact": REFERENCE.model_dump(mode="json"),
            "declaration": {"schema_version": "1", "transformation": {
                "transformation_id": "fixture", "version": "1", "sha256": "c" * 64},
                "inputs": [artifact("source").model_dump(mode="json")]}}


@contextmanager
def peer(overrides=None, delay=0, trickle=False):
    replies = {PATH: (200, REFERENCE.model_dump_json().encode()), PATH + "/content": (200, CONTENT),
               PATH + "/derivation": (200, json.dumps(proof()).encode())}
    replies.update(overrides or {})
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            calls.append((self.path, self.headers.get("Authorization")))
            status, content = replies.get(self.path, (404, b""))
            if delay:
                time.sleep(delay)
            try:
                if trickle:
                    for byte in b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n":
                        self.connection.sendall(bytes([byte]))
                        time.sleep(0.03)
                    return
                self.send_response(status)
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(content)
            except (OSError, ConnectionError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    try:
        yield AssessmentDataReader(f"http://127.0.0.1:{server.server_port}", TOKEN, SCOPE), calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_public_read_pins_metadata_content_origin_and_scope_with_only_per_attempt_cache():
    with peer() as (reader, calls):
        body, derivation = reader.published(REFERENCE, frozenset({"publisher"}))
        assert body == CONTENT and derivation.origin.actor_id == "publisher"
        assert reader.published(REFERENCE, frozenset({"publisher"})) == (body, derivation)
        assert reader.consumed == (REFERENCE,)
        assert [path for path, _ in calls] == [PATH, PATH + "/content", PATH + "/derivation"]
        assert all(auth == "Bearer " + TOKEN for _, auth in calls)
        with pytest.raises(AssessmentError, match="untrusted_publisher"):
            reader.published(REFERENCE, frozenset({"another"}))


@pytest.mark.parametrize(("status", "code", "retryable"), [
    (401, "peer_access_denied", False), (403, "peer_access_denied", False),
    (404, "reference_unavailable", False), (503, "peer_unavailable", True),
    (302, "peer_unavailable", True),
])
def test_denial_and_absence_are_distinct_from_operational_outage(status, code, retryable):
    with peer({PATH: (status, b"private-peer-diagnostic")}) as (reader, calls):
        with pytest.raises(AssessmentError, match=code) as caught:
            reader.read(REFERENCE)
        assert isinstance(caught.value, AssessmentPeerUnavailable) is retryable
        assert TOKEN not in str(caught.value) and "diagnostic" not in str(caught.value)
        assert len(calls) == 1


def test_readable_lineage_never_bypasses_denied_current_content():
    with peer({PATH + "/content": (403, b"")}) as (reader, calls):
        with pytest.raises(AssessmentError, match="peer_access_denied"):
            reader.published(REFERENCE, frozenset({"publisher"}))
        assert reader.consumed == ()
        assert all(path != PATH + "/derivation" for path, _ in calls)


@pytest.mark.parametrize(("path", "body", "code"), [
    (PATH, b'{"wire_version":1,"wire_version":2}', "peer_protocol_error"),
    (PATH, b'{"value":NaN}', "peer_protocol_error"),
    (PATH, b'not-json', "peer_protocol_error"),
    (PATH, artifact("another").model_dump_json().encode(), "artifact_reference_mismatch"),
    (PATH + "/content", b"x" * len(CONTENT), "artifact_integrity_mismatch"),
    (PATH + "/content", CONTENT + b"x", "peer_response_limit"),
])
def test_untrusted_response_bytes_cannot_become_valid_observations(path, body, code):
    with peer({path: (200, body)}) as (reader, _):
        with pytest.raises(AssessmentError, match=code):
            reader.read(REFERENCE)
        assert reader.consumed == ()


@pytest.mark.parametrize("mutation", [
    lambda p: p.update(artifact=artifact("other").model_dump(mode="json")),
    lambda p: p["origin"].update(scope=OTHER.model_dump(mode="json")),
    lambda p: p["origin"].update(command_family="artifacts.begin_upload"),
    lambda p: p["declaration"].update(inputs=[artifact("input", scope=OTHER).model_dump(mode="json")]),
])
def test_lineage_must_identify_exact_output_scope_and_derived_command(mutation):
    value = proof()
    mutation(value)
    with peer({PATH + "/derivation": (200, json.dumps(value).encode())}) as (reader, _):
        with pytest.raises(AssessmentError, match="derivation_reference_mismatch"):
            reader.published(REFERENCE, frozenset({"publisher"}))


def test_equivocal_scope_identity_and_size_rejected_before_peer_io():
    with peer() as (reader, calls):
        for reference, code in [(REFERENCE.model_copy(update={"scope": OTHER}), "artifact_scope_mismatch"),
                                (artifact("huge", size_bytes=16 * 1024 * 1024 + 1), "artifact_read_limit")]:
            with pytest.raises(AssessmentError, match=code):
                reader.read(reference)
        assert not calls
        reader.read(REFERENCE)
        with pytest.raises(AssessmentError, match="artifact_identity_conflict"):
            reader.read(REFERENCE.model_copy(update={"sha256": "d" * 64}))
        assert len(calls) == 2


def test_input_call_and_total_byte_budgets_are_finite():
    with peer() as (reader, _):
        for i in range(128):
            reader._admit(artifact(f"input-{i}"))
        with pytest.raises(AssessmentError, match="assessment_input_limit"):
            reader.read(REFERENCE)
    with peer() as (reader, _):
        reader._calls = 384
        with pytest.raises(AssessmentError, match="peer_call_limit"):
            reader.read(REFERENCE)
    with peer() as (reader, _):
        reader._bytes = 32 * 1024 * 1024
        with pytest.raises(AssessmentError, match="peer_response_limit"):
            reader.read(REFERENCE)


def test_overall_deadline_interrupts_an_active_header_wait():
    with peer(delay=2) as (reader, calls):
        reader._deadline = time.monotonic() + 0.5
        start = time.monotonic()
        with pytest.raises(AssessmentPeerUnavailable):
            reader.read(REFERENCE)
        assert time.monotonic() - start < 1.5
        assert len(calls) == 1
        # Test expired admission separately: an OS failure may precede the deadline.
        reader._deadline = time.monotonic() - 1
        with pytest.raises(AssessmentPeerUnavailable, match="peer_deadline"):
            reader.read(REFERENCE)


@pytest.mark.parametrize("endpoint", ["http://example.com:80", "https://127.0.0.1:443", "http://127.0.0.1",
                                       "http://127.0.0.1:bad", "http://user@127.0.0.1:80", "http://127.0.0.1:80/a"])
def test_only_explicit_loopback_owner_endpoint_is_accepted(endpoint):
    with pytest.raises(AssessmentError, match="explicit_loopback_peer_required"):
        AssessmentDataReader(endpoint, TOKEN, SCOPE)


@pytest.mark.parametrize("token", ["short", "x" * 31 + "\n", None])
def test_invalid_credentials_are_not_embedded_in_errors(token):
    with pytest.raises(AssessmentError, match="invalid_peer_credential"):
        AssessmentDataReader("http://127.0.0.1:80", token, SCOPE)


def test_invalid_utf8_is_retryable_peer_protocol_failure():
    with pytest.raises(AssessmentPeerUnavailable, match="peer_protocol_error"):
        _decode(type(METHOD), b"\xff")


def test_content_is_reassembled_across_multiple_bounded_reads():
    content = b"x" * 131073
    reference = REFERENCE.model_copy(update={"size_bytes": len(content),
                                             "sha256": hashlib.sha256(content).hexdigest()})
    with peer({PATH: (200, reference.model_dump_json().encode()), PATH + "/content": (200, content)}) as (reader, _):
        assert reader.read(reference) == content
        assert reader.consumed == (reference,)


def test_trickling_headers_cannot_reset_the_whole_attempt_deadline():
    with peer(trickle=True) as (reader, calls):
        reader._deadline = time.monotonic() + 0.3
        start = time.monotonic()
        with pytest.raises(AssessmentPeerUnavailable):
            reader.read(REFERENCE)
        assert len(calls) == 1
        assert time.monotonic() - start < 1
