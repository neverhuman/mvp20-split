import json
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from types import SimpleNamespace as NS

import pytest
from amphora_contracts_core import ArtifactRef, Scope
from amphora_contracts_tools import Invocation, ReleaseDescriptor
from amphora_tool_protocol import TransportLost, WorkerIdentity


@pytest.fixture
def descriptor():
    schema = {"schema_id": "fixture.record", "version": "1", "sha256": "c" * 64}
    port = {"schema_ref": schema, "representation": "fixture", "unit": "1", "required": True}
    return ReleaseDescriptor.model_validate_json(json.dumps({
        "schema_version": "1", "tool": {"schema_version": "1", "binding": {"capability_id": "fixture.bundle",
        "release": "0.1.0", "image_sha256": "a" * 64, "contract_version": "1"}, "purpose": "Two-input lifecycle fixture",
        "applicability": ["synthetic"], "inputs": [{"name": "parameters", **port}, {"name": "policy", **port}],
        "outputs": [{"name": "result", **port}], "side_effects": "pure", "checkpoint_schema": None},
        "resources": {"architectures": ["x86_64"], "operating_systems": ["linux"], "cpu_millicores": 1000,
        "memory_mib": 128, "gpu_count": 0, "timeout_seconds": 60, "max_parallel_invocations": 1, "max_batch_size": 1},
        "egress": {"mode": "deny"}, "checkpoint": {"mode": "none", "readable_schema_sha256": []},
        "reproducibility": "deterministic", "authority_ceiling": "synthetic_only", "examples": ["fixture"], "anti_examples": ["science"]}))


class Runtime:
    def __init__(self, descriptor):
        self.identity = WorkerIdentity("worker", Scope(tenant_id="fixture", project_id="multi-input"))
        self.descriptor = descriptor
        self.revoked = False
        self.no_work = False
        self.completion_unknown = False
        self.revision = 0
        self.completions = []
        self.data = {"parameters": b'{"x":2}', "policy": b'{"fixture":true}'}
        references = [ArtifactRef(artifact_id=name, scope=self.identity.scope, sha256=sha256(self.data[name]).hexdigest(),
                                  size_bytes=len(self.data[name]), media_type="application/json", schema_ref=port.schema_ref)
                      for name, port in zip(self.data, descriptor.tool.inputs, strict=True)]
        self.invocation = Invocation.model_validate_json(json.dumps({"schema_version": "1", "scope": self.identity.scope.model_dump(mode="json"),
            "run_id": "run", "node_id": "node", "activation_id": "activation", "invocation_id": "invocation",
            "attempt_id": "attempt", "fence": 1, "tool": descriptor.tool.binding.model_dump(mode="json"),
            "inputs": [{"port": ref.artifact_id, "artifact": ref.model_dump(mode="json")} for ref in references],
            "timeout_seconds": 60, "grant_id": "grant"}))

    def claim(self, *_args, **_kwargs):
        return NS(outcome=NS(status="no_eligible_work" if self.no_work else "claimed", invocation=self.invocation,
                             lease_expires_at=(datetime.now(UTC) + timedelta(seconds=30)).isoformat()))

    def renew(self, _attempt, _command, **kwargs):
        kwargs["guard"]()
        self.revision += 1
        return NS(outcome=NS(committed=NS(revision=self.revision)))

    def run(self, _run):
        return NS(status="running", revision=self.revision, activations=[NS(invocation_id="invocation", status="leased",
            fence=2 if self.revoked else 1, latest_attempt=NS(attempt_id="attempt", fence=1, worker_id="worker", status="leased",
                lease_expires_at=(datetime.now(UTC) + timedelta(seconds=30)).isoformat(),
                deadline=(datetime.now(UTC) + timedelta(seconds=60)).isoformat()))])

    def complete(self, command, command_id, **kwargs):
        kwargs["guard"]()
        self.completions.append((command, command_id))
        if self.completion_unknown:
            raise TransportLost("completion_unknown")
        return NS(outcome=NS(binding=NS(operation_id="completion-fixture")))


class Artifacts:
    def __init__(self, runtime):
        self.runtime, self.identity = runtime, runtime.identity
        self.events = []
        self.corrupt = False
        self.revoke_after_read = False
        self.stream_error = None

    def read(self, reference):
        self.events.append("read:" + reference.artifact_id)
        if self.revoke_after_read:
            self.runtime.revoked = True
        return b"corrupted" if self.corrupt else self.runtime.data[reference.artifact_id]

    def begin(self, content, command_id, **kwargs):
        kwargs["guard"]()
        self.events.append("begin:" + command_id)
        self.content = content
        return NS(upload_id="fixture-upload")

    def stream(self, _upload, output, **kwargs):
        kwargs["guard"]()
        self.events.append("stream")
        if self.stream_error:
            raise self.stream_error
        self.output = output

    def finalize(self, _upload, command_id, **kwargs):
        kwargs["guard"]()
        self.events.append("finalize:" + command_id)
        return NS(artifact=ArtifactRef(artifact_id="result", scope=self.identity.scope,
                  sha256=self.content.sha256, size_bytes=self.content.size_bytes, media_type="application/json",
                  schema_ref=self.content.schema_ref))


@pytest.fixture
def peers(descriptor):
    runtime = Runtime(descriptor)
    return runtime, Artifacts(runtime)
