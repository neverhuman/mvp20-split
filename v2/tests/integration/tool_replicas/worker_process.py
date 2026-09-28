"""Test-only response barriers around an installed public SDK and actual tool kernel."""

import importlib
import importlib.util
import json
import os
import sys
from pathlib import Path

from amphora_tool_protocol import (
    ArtifactClient,
    HttpTransport,
    ProtocolError,
    PureToolWorker,
    RuntimeClient,
    WorkerConfig,
    WorkerIdentity,
)


class BarrierTransport:
    def __init__(self, endpoint, marker, stages):
        self.transport = HttpTransport(endpoint.endpoint, os.environ[endpoint.token_env])
        self.marker, self.stages = marker, stages

    def request(self, method, path, body=None, **kwargs):
        reply = self.transport.request(method, path, body, **kwargs)
        if method == "POST" and path in self.stages and reply.status == 200:
            packet = {"stage": self.stages[path], "response": json.loads(reply.body)}
            temporary = self.marker.with_suffix(".tmp")
            temporary.write_text(json.dumps(packet), encoding="utf-8")
            temporary.replace(self.marker)
            assert sys.stdin.readline().strip() == "continue", "Test controller closed the barrier"
        return reply


def main():
    module, config_path, marker_path = sys.argv[1:]
    adapter = importlib.import_module(module + ".adapter")
    metadata = importlib.import_module(module + ".metadata")
    assert Path(adapter.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
    for absent in ("sqlalchemy", "amphora_campaign_runtime", "amphora_data_artifacts", "amphora_capability_registry"):
        assert importlib.util.find_spec(absent) is None
    assert not any("DATABASE" in key or "MIGRATION" in key or key == "PYTHONPATH" for key in os.environ)
    config = WorkerConfig.model_validate_json(Path(config_path).read_bytes())
    marker = Path(marker_path)
    identity = WorkerIdentity(config.actor_id, config.scope)
    worker = PureToolWorker(
        RuntimeClient(BarrierTransport(config.runtime, marker, {"/v1/invocations/claim": "claimed"}), identity),
        ArtifactClient(BarrierTransport(config.artifacts, marker, {"/v1/artifacts/finalize": "published"}), identity),
        metadata.descriptor(config.image_sha256), adapter.execute, lease_seconds=config.lease_seconds)
    try:
        print(json.dumps(worker.run_once(config.run_id)), flush=True)
    except ProtocolError:
        print(json.dumps({"status": "authority_or_transport_lost"}), flush=True)
        raise SystemExit(3) from None


if __name__ == "__main__":
    main()
