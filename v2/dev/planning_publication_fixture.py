"""Public HTTP setup for the installed Planning/Data publication acceptance gate."""

import hashlib
import json
import secrets
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from amphora_contracts_artifacts import ContentDescriptor
from amphora_contracts_core import Scope
from amphora_tool_protocol import ArtifactClient, HttpTransport, WorkerIdentity

ROOT = Path(__file__).absolute().parents[1]
PLANNING = ROOT / "services/agent_planning"


class DataHost:
    def __init__(self, python, config, environment, token):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        self.endpoint, self.token = f"http://127.0.0.1:{port}", token
        self.process = subprocess.Popen([str(python), "-I", "-m", "amphora_data_artifacts", "serve",
            "--config", str(config), "--port", str(port)], env=environment,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if self.process.poll() is not None:
                    raise RuntimeError("Data publication host exited before readiness")
                try:
                    if self.call("GET", "/ready")["ready"]:
                        return
                except (urllib.error.URLError, TimeoutError):
                    pass
                time.sleep(0.05)
            raise RuntimeError("Data publication readiness deadline")
        except BaseException:
            self.close()
            raise

    def call(self, method, path, body=None):
        payload = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(self.endpoint + path, payload, method=method,
            headers={"Authorization": "Bearer " + self.token, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                data = response.read(1048577)
                assert len(data) <= 1048576
                return json.loads(data)
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"Data public fixture request failed: {method} {path} status={error.code}") from None

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=10)


def configure(output, scope):
    token = secrets.token_urlsafe(32)
    storage = output / "artifact-bytes"
    storage.mkdir()
    schema_path = output / "extraction-trace-v1.schema.json"
    schema = (PLANNING / "src/amphora_agent_planning/publication/extraction-trace-v1.schema.json").read_bytes()
    schema_path.write_bytes(schema)
    text_profile = {"media_type": "text/plain", "schema_id": "fixture.text", "version": "1",
                    "sha256": hashlib.sha256(b'{"type":"string"}').hexdigest()}
    profile = {"media_type": "application/json", "schema_id": "planning.extraction-trace-content",
               "version": "1", "sha256": hashlib.sha256(schema).hexdigest(), "schema_path": schema_path.name}
    config = {"database_url_env": "PUBLICATION_DATA_DATABASE", "storage_root": str(storage), "acquisition": True,
              "profiles": [text_profile, profile], "limits": {"max_bytes": 1048576, "scope_bytes": 67108864},
              "principals": [{"token_env": "PUBLICATION_DATA_TOKEN", "actor_id": "fixture", "scope": scope,
                              "actions": ["upload", "finalize", "read", "acquire", "source_history",
                                          "manage_source_rights"]}]}
    path = output / "data-host.json"
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return path, token, text_profile


def populate(host, output, scope, profile):
    raw = json.loads((PLANNING / "tests/extraction/fixtures/extraction.json").read_bytes())
    client = ArtifactClient(HttpTransport(host.endpoint, host.token), WorkerIdentity("fixture", Scope.model_validate(scope)))

    def publish(key, body, media="text/plain", schema=None):
        descriptor = {"sha256": hashlib.sha256(body).hexdigest(), "size_bytes": len(body), "media_type": media,
                      "schema_ref": schema or {k: profile[k] for k in ("schema_id", "version", "sha256")}}
        upload = client.begin(ContentDescriptor.model_validate_json(json.dumps(descriptor)), "input-" + key)
        client.stream(upload, body)
        return client.finalize(upload, "finalize-" + key).artifact.model_dump(mode="json")

    bodies = {key: (key + " synthetic fixture").encode() for key in ("objective", "policy", "configuration")}
    bodies["prompt"] = (PLANNING / "src/amphora_agent_planning/extraction/prompts/domain-decomposition-v1.txt").read_bytes()
    bodies["source-utf8"] = raw["source_text"].encode("utf-8")
    refs = {key: publish(key, body) for key, body in bodies.items()}

    def replace(value):
        if isinstance(value, dict):
            if "artifact_id" in value and value["artifact_id"] in refs:
                return refs[value["artifact_id"]]
            if set(value) == {"tenant_id", "project_id"}:
                return dict(scope)
            return {key: replace(item) for key, item in value.items()}
        if isinstance(value, list):
            return [replace(item) for item in value]
        return value
    raw = replace(raw)
    rights = {"wire_version": "1", "reference": {"scope": scope, "rights_id": "source", "revision": 1},
              "supersedes": None, "status": "granted", "allowed_uses": ["read", "process"],
              "expires_at": None, "retention": "retain_audit_payload"}
    host.call("POST", "/v1/acquisition/rights", rights)
    source = {"wire_version": "1", "reference": raw["task"]["sources"][0]["source"],
              "delivery": {"issuer_id": "fixture", "delivery_id": "actual-input"},
              "method": {"connector_id": "fixture", "connector_version": "1",
                         "configuration_sha256": hashlib.sha256(b"{}").hexdigest(), "format": "utf8_document"},
              "rights": rights["reference"], "supersedes": None, "completeness": "partial"}
    prepared = host.call("POST", "/v1/acquisition/prepare", source)
    converted = publish("converted", prepared["content_json_utf8"].encode("utf-8"), "application/json", prepared["schema_ref"])
    trace = host.call("POST", "/v1/acquisition/retain", {"wire_version": "1", "source": source,
                     "trace_id": "conversion", "output": converted})
    raw["task"]["sources"][0]["conversion_traces"] = [trace]
    path = output / "actual-extraction.json"
    path.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path, rights, source, tuple([*refs.values(), converted])
