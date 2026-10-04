import hashlib
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from amphora_agent_planning.campaign_data_access import (
    ArtifactSelection,
    CampaignArtifactReader,
)
from amphora_agent_planning.source_access import DataReader

from ..campaign_context.test_selection import SCOPE, request


def ref(name="one", body=b"data"):
    base = request().document().context.objective
    return base.model_copy(update={"artifact_id": name, "sha256": hashlib.sha256(body).hexdigest(), "size_bytes": len(body)})


def selected(*references):
    return ArtifactSelection.bind(request(), tuple(references) or (ref(),))


class Data:
    def __init__(self):
        self.calls, self.errors, self.content_value, self.actual = [], {}, b"data", None

    def artifact(self, reference, budget):
        budget.start()
        self.calls.append(("metadata", reference.artifact_id))
        if reference.artifact_id in self.errors:
            raise self.errors[reference.artifact_id]
        return reference if self.actual is None else self.actual

    def content(self, reference, budget):
        budget.start()
        self.calls.append(("processing", reference.artifact_id))
        budget.consume(len(self.content_value))
        return self.content_value


def test_bound_selection_and_successful_bytes_are_immutable():
    chosen = selected()
    assert len(chosen.sha256) == 64
    result = CampaignArtifactReader(Data()).read(chosen)
    assert result.records[0].reference == ref() and result.records[0].body == b"data" and not result.failures
    assert result.calls == 2 and result.bytes == 4
    assert result.selection == chosen


@pytest.mark.parametrize("reason", ["source_access_denied", "source_reference_unavailable", "source_peer_protocol"])
def test_one_unavailable_artifact_preserves_other_useful_content(reason):
    data = Data()
    data.errors["one"] = ValueError(reason)
    result = CampaignArtifactReader(data).read(selected(ref(), ref("two")))
    assert [r.reference.artifact_id for r in result.records] == ["two"]
    assert [(f.reference.artifact_id, f.code) for f in result.failures] == [("one", reason)]


@pytest.mark.parametrize("reason", ["source_peer_unavailable", "source_review_deadline", "source_review_byte_limit", "source_review_call_limit"])
def test_global_limits_stop_new_calls_without_inventing_success(reason):
    data = Data()
    data.errors["one"] = ValueError(reason)
    result = CampaignArtifactReader(data).read(selected(ref(), ref("two")))
    assert not result.records and len(result.failures) == 2 and {f.code for f in result.failures} == {reason}
    assert len(data.calls) == 1


@pytest.mark.parametrize("fault,code", [("identity", "source_artifact_binding"), ("digest", "source_artifact_bytes"),
    ("length", "source_artifact_bytes"), ("boolean", "campaign_artifact_invalid")])
def test_misbound_or_forged_content_never_enters_context(fault, code):
    data = Data()
    if fault == "identity":
        data.actual = ref("substituted")
    elif fault == "digest":
        data.content_value = b"evil"
    elif fault == "length":
        data.content_value = b"longer"
    else:
        data.actual = ref().model_copy(update={"size_bytes": True})
    result = CampaignArtifactReader(data).read(selected())
    assert not result.records and result.failures[0].code == code


def test_no_cross_operation_cache_and_read_revocation_is_observed():
    data = Data()
    reader, chosen = CampaignArtifactReader(data), selected()
    first = reader.read(chosen)
    data.errors["one"] = ValueError("source_access_denied")
    second = reader.read(chosen)
    assert first.records[0].body == b"data" and not second.records
    assert second.failures[0].code == "source_access_denied" and len(data.calls) == 3


def test_empty_selection_has_no_reads_and_unknown_bugs_propagate():
    assert CampaignArtifactReader(None).read(ArtifactSelection.bind(request(), ())).records == ()
    data = Data()
    data.errors["one"] = ValueError("implementation_bug")
    with pytest.raises(ValueError, match="implementation_bug"):
        CampaignArtifactReader(data).read(selected())


@pytest.mark.parametrize("fault", ["duplicate", "count", "scope", "size", "boolean", "sequence"])
def test_selection_rejects_before_any_read(fault):
    references = (ref(),)
    if fault == "duplicate":
        references *= 2
    elif fault == "count":
        references = tuple(ref(str(n)) for n in range(129))
    elif fault == "scope":
        references = (ref().model_copy(update={"scope": SCOPE.model_copy(update={"project_id": "foreign"})}),)
    elif fault == "size":
        references = (ref().model_copy(update={"size_bytes": 4194305}),)
    elif fault == "boolean":
        references = (ref().model_copy(update={"size_bytes": True}),)
    else:
        references = [ref()]
    with pytest.raises(ValueError):
        ArtifactSelection.bind(request(), references)


def test_final_deadline_check_excludes_late_content():
    class Late(Data):
        def content(self, reference, budget):
            body = super().content(reference, budget)
            budget.deadline = 0
            return body
    result = CampaignArtifactReader(Late()).read(selected())
    assert not result.records and result.failures[0].code == "source_review_deadline"


def test_real_http_reads_only_processing_content_and_rechecks_each_preparation():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            self.server.calls.append((self.path, self.headers.get("Authorization")))
            processing = self.path.endswith("/processing-content")
            content = b"data" if processing else ref().model_dump_json().encode()
            self.send_response(403 if processing and self.server.denied else 200)
            self.send_header("Content-Type", "text/plain" if processing else "application/json")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
    host = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    host.daemon_threads, host.denied, host.calls = True, False, []
    thread = threading.Thread(target=host.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    try:
        reader = CampaignArtifactReader(DataReader(f"http://127.0.0.1:{host.server_port}", "t" * 32))
        first = reader.read(selected())
        host.denied = True
        second = reader.read(selected())
        assert first.records[0].body == b"data" and second.failures[0].code == "source_access_denied"
        assert host.calls == [(path, "Bearer " + "t" * 32) for path in
            ("/v1/artifacts/one", "/v1/artifacts/one/processing-content") * 2]
    finally:
        host.shutdown()
        host.server_close()
        thread.join(2)


def test_forged_serialized_selection_is_bounded_before_expansion():
    with pytest.raises(ValueError, match="campaign_artifact_selection_size"):
        CampaignArtifactReader(None).read(ArtifactSelection(request(), b" " * 262145))
    with pytest.raises(ValueError, match="campaign_artifact_count"):
        CampaignArtifactReader(None).read(ArtifactSelection(request(), json.dumps([{}] * 129).encode()))
    with pytest.raises(ValueError, match="campaign_artifact_budget"):
        CampaignArtifactReader(None).read(selected(), object())
