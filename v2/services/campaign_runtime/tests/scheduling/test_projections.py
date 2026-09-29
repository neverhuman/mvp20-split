"""Bounded immutable Artifact HTTP reads and typed finite predicate evaluation."""

import hashlib
import json
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest
from amphora_campaign_runtime.coordinator.bindings import ValueEnvironment
from amphora_campaign_runtime.coordinator.predicates import PredicateValues, ProjectionNeeded
from amphora_campaign_runtime.coordinator.projections import ArtifactProjections, ProjectionUnavailable
from amphora_campaign_runtime.coordinator.values import BoundValues
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_contracts_core import ArtifactRef

from ..compiler.conftest import definition
from .test_advancement import admit, advance, table


@pytest.fixture
def artifact_http():
    state = {"body": b'{"values":[1.5],"a":2,"b":0}', "requests": [], "metadata": {}, "redirect": False}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            state["requests"].append((self.path, self.headers.get("Authorization")))
            if state["redirect"]:
                self.send_response(302)
                self.send_header("Location", "/unexpected")
                self.end_headers()
                return
            body = state["body"] if self.path.endswith("/content") else json.dumps(state["metadata"]).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    state["client"] = ArtifactProjections(f"http://127.0.0.1:{server.server_port}", "p" * 32)
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def reference(graph, state):
    raw = dict(graph.payload["inputs"][0]["value"]["artifact"])
    raw.update(size_bytes=len(state["body"]), sha256=hashlib.sha256(state["body"]).hexdigest())
    state["metadata"] = raw
    return ArtifactRef.model_validate_json(json.dumps(raw))


@pytest.mark.parametrize("case,expected", [("valid", None), ("digest", "projection_artifact_integrity"),
    ("binding", "projection_artifact_binding_mismatch"), ("duplicate", "projection_artifact_json_invalid"),
    ("nonfinite", "projection_artifact_json_invalid"), ("oversize", "projection_payload_too_large")])
def test_http_projection_verifies_binding_bytes_and_json(graph_env, artifact_http, case, expected):
    state = artifact_http
    if case == "duplicate":
        state["body"] = b'{"a":1,"a":2}'
    if case == "nonfinite":
        state["body"] = b'{"a":NaN}'
    ref = reference(graph_env, state)
    if case == "digest":
        state["body"] = b'x' * len(state["body"])
    if case == "binding":
        state["metadata"] = {**state["metadata"], "sha256": "f" * 64}
    if case == "oversize":
        state["body"] = b'x' * 262145
    if expected:
        with pytest.raises(TransitionError, match=expected):
            state["client"].fetch(ref)
    else:
        assert state["client"].fetch(ref) == {"values": [Decimal("1.5")], "a": 2, "b": 0}
    assert all(token == "Bearer " + "p" * 32 for _, token in state["requests"])


def test_redirect_is_not_followed_or_given_credentials(graph_env, artifact_http):
    ref = reference(graph_env, artifact_http)
    artifact_http["redirect"] = True
    with pytest.raises(ProjectionUnavailable):
        artifact_http["client"].fetch(ref)
    assert len(artifact_http["requests"]) == 1


def artifact_branch(raw):
    raw["body"]["inputs"] = raw["body"]["inputs"][:1]
    raw["body"]["nodes"][0]["predicate"] = {"kind": "compare", "left": {
        "source": {"kind": "input", "name": "parameters"}, "path": ["a"],
        "value_type": {"kind": "scalar", "scalar": "number", "unit": "1"}},
        "operator": "gt", "right": {"kind": "number", "value": 1, "unit": "1"}}


def test_projection_fetch_has_no_runtime_run_lock_and_failure_retries_same_command(graph_env, artifact_http):
    from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
    from sqlalchemy import text

    graph, state = graph_env, artifact_http
    ref = reference(graph, state)
    graph.payload["inputs"][0]["value"]["artifact"] = ref.model_dump(mode="json")
    run = admit(graph, 1, graph.payload["inputs"], modify=artifact_branch)
    command = graph.command("graph.advance", {"run_id": run})

    class Probe:
        def fetch(self, artifact):
            with graph.env.engine.begin() as conn:
                conn.execute(text("SELECT run_id FROM runtime.runs WHERE run_id=:run FOR UPDATE NOWAIT"), {"run": run})
            return state["client"].fetch(artifact)

    state["redirect"] = True
    service = GraphAdvancer(graph.env.engine, Probe())
    with pytest.raises(ProjectionUnavailable):
        service.advance(graph.env.principal, command)
    assert {row["status"] for row in table(graph, run, "graph_nodes")} == {"ready", "waiting"}
    state["redirect"] = False
    assert service.advance(graph.env.principal, command).outcome.status == "accepted"
    chosen = next(row for row in table(graph, run, "graph_nodes") if row["node_id"] == "choose")
    assert chosen["state"] == {"route": "true"}


@pytest.mark.parametrize("payload,reason", [({}, "projection_value_missing"), ({"a": True}, "projection_value_type")])
def test_missing_or_wrong_projection_blocks_never_defaults_false(graph_env, artifact_http, payload, reason):
    graph, state = graph_env, artifact_http
    state["body"] = json.dumps(payload).encode()
    ref = reference(graph, state)
    graph.payload["inputs"][0]["value"]["artifact"] = ref.model_dump(mode="json")
    run = admit(graph, 1, graph.payload["inputs"], modify=artifact_branch)
    assert advance(graph, run, projections=state["client"]).status == "blocked"
    chosen = next(row for row in table(graph, run, "graph_nodes") if row["node_id"] == "choose")
    assert chosen["reason_code"] == reason and chosen["state"] == {}


@pytest.mark.parametrize("operator,result", [("eq", False), ("ne", True), ("lt", False), ("le", False), ("gt", True), ("ge", True)])
def test_predicate_operator_results_are_independently_specified(graph_env, operator, result):
    raw = graph_env.source.raw[1]
    artifact_branch(raw)
    raw["body"]["nodes"][0]["predicate"]["operator"] = operator
    predicate = definition(raw).body.nodes[0].predicate
    inputs = BoundValues.from_records(graph_env.payload["inputs"])
    env = ValueEnvironment(inputs, {})
    artifact = inputs.bindings[0].value.artifact
    with pytest.raises(ProjectionNeeded):
        PredicateValues(env, {}).evaluate(predicate)
    assert PredicateValues(env, {artifact.model_dump_json(): {"a": Decimal("1.0000000000000000001")}}).evaluate(predicate) is result
