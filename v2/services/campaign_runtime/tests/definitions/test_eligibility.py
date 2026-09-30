"""Public-peer policy tests; these replies do not substitute for actual Registry acceptance."""

import json
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from types import SimpleNamespace

import pytest
from amphora_campaign_runtime.definitions.eligibility import RegistryEligibility
from amphora_campaign_runtime.definitions.eligibility.observations import (
    EligibilityUnavailable,
)
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_contracts_core import Scope
from amphora_contracts_tools import RegistryReceipt


def candidate(tool, scope, at=None):
    at = at or datetime.now(UTC)
    return RegistryReceipt.model_validate_json(
        json.dumps(
            {
                "operation_id": "registry-observation",
                "status": "accepted",
                "reason_code": "candidate",
                "release": {
                    "scope": scope.model_dump(),
                    "descriptor": tool.descriptor.model_dump(mode="json"),
                    "lock": tool.lock.model_dump(mode="json"),
                    "revision": 2,
                    "status": "active",
                },
                "deployment": None,
                "heartbeat": None,
                "decision": {
                    "status": "candidate",
                    "assessed_at": at.isoformat(),
                    "capacity_valid_until": (at + timedelta(seconds=60)).isoformat(),
                    "admission": {
                        "status": "allowed",
                        "reason_codes": ["synthetic_fixture_only"],
                    },
                    "observations": {
                        "scope": scope.model_dump(),
                        "release": tool.lock.model_dump(mode="json"),
                        "policy_sha256": "a" * 64,
                        "structural": {"status": "valid", "findings": []},
                        "scientific": {
                            "status": "eligible",
                            "reason_codes": ["synthetic_fixture_only"],
                        },
                        "capacity": {"status": "available", "reason_codes": []},
                    },
                },
            }
        )
    )


def plan(tool):
    scope = Scope(tenant_id="synthetic", project_id="eligibility")
    return SimpleNamespace(
        draft=SimpleNamespace(
            content=SimpleNamespace(definition=SimpleNamespace(scope=scope))
        ),
        universe=SimpleNamespace(releases=(tool,)),
        entry=SimpleNamespace(
            plan=SimpleNamespace(
                document=SimpleNamespace(lock=SimpleNamespace(tools=(tool.lock,)))
            )
        ),
    )


def client():
    return RegistryEligibility("http://127.0.0.1:1", "s" * 32, "selector")


def test_exact_observation_and_expiry_do_not_grant_a_reservation(
    compiler_env, monkeypatch
):
    reviewed = plan(compiler_env.tool)
    scope = reviewed.draft.content.definition.scope
    peer = client()
    observed = []

    def resolve(command, timeout):
        observed.append(command)
        assert 0 < timeout <= 10
        payload = json.loads(command.canonical_bytes)["payload"]
        assert payload["context"] == "synthetic-tests"
        assert payload["release"] == compiler_env.tool.lock.model_dump(mode="json")
        return candidate(compiler_env.tool, scope)

    monkeypatch.setattr(peer, "_resolve", resolve)
    first = peer.observe(reviewed)[0]
    second = peer.observe(reviewed)[0]
    assert first.command.identity != second.command.identity
    first.require_fresh(first.receipt.decision.assessed_at)
    assert first.record()["request_sha256"] == observed[0].sha256
    for instant in [
        first.receipt.decision.assessed_at - timedelta(microseconds=1),
        first.receipt.decision.assessed_at + timedelta(seconds=6),
        first.receipt.decision.capacity_valid_until,
    ]:
        with pytest.raises(TransitionError, match="eligibility_expired"):
            first.require_fresh(instant)


@pytest.mark.parametrize(
    "change",
    [
        "scope",
        "lock",
        "inactive",
        "scientific",
        "policy",
        "expiry",
        "missing",
        "rejected",
    ],
)
def test_mismatched_or_ineligible_observation_fails_closed(
    compiler_env, monkeypatch, change
):
    reviewed = plan(compiler_env.tool)
    raw = json.loads(
        candidate(
            compiler_env.tool, reviewed.draft.content.definition.scope
        ).model_dump_json()
    )
    if change == "scope":
        raw["release"]["scope"]["project_id"] = "foreign"
    if change == "lock":
        raw["decision"]["observations"]["release"]["descriptor_sha256"] = "f" * 64
    if change == "inactive":
        raw["release"]["status"] = "revoked"
    if change == "scientific":
        raw["decision"]["observations"]["scientific"]["status"] = "unreviewed"
    if change == "policy":
        raw["decision"]["admission"]["status"] = "denied"
    if change == "expiry":
        raw["decision"]["capacity_valid_until"] = raw["decision"]["assessed_at"]
    if change == "missing":
        raw["decision"] = None
    if change == "rejected":
        raw["status"] = "rejected"
    peer = client()
    monkeypatch.setattr(
        peer,
        "_resolve",
        lambda *args: RegistryReceipt.model_validate_json(json.dumps(raw)),
    )
    with pytest.raises(
        TransitionError if change == "rejected" else EligibilityUnavailable
    ):
        peer.observe(reviewed)


def test_transport_bounds_denial_redirect_invalid_and_lost_response(compiler_env):
    reviewed = plan(compiler_env.tool)
    scope = reviewed.draft.content.definition.scope
    state = {
        "status": 200,
        "body": candidate(compiler_env.tool, scope).model_dump_json().encode(),
        "requests": [],
    }

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            assert self.path == "/v1/registry/resolve"
            assert self.headers["Authorization"] == "Bearer " + "s" * 32
            state["requests"].append(
                self.rfile.read(int(self.headers["Content-Length"]))
            )
            self.send_response(state["status"])
            self.send_header("Location", "/leak")
            self.end_headers()
            self.wfile.write(state["body"])

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        peer = RegistryEligibility(
            f"http://127.0.0.1:{server.server_port}", "s" * 32, "selector"
        )
        assert len(peer.observe(reviewed)) == 1
        for status, body in [
            (403, b"private detail"),
            (302, b""),
            (200, b"x" * 262145),
            (200, b"{}"),
            (200, b"\xff"),
        ]:
            state.update(status=status, body=body)
            with pytest.raises(EligibilityUnavailable):
                peer.observe(reviewed)
        assert len(state["requests"]) == 6
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://remote.invalid",
        "https://name:secret@host",
        "https://host/other",
        "https://host?query=1",
    ],
)
def test_peer_configuration_rejects_unsafe_origins(endpoint):
    with pytest.raises(ValueError):
        RegistryEligibility(endpoint, "s" * 32, "selector")
