"""Test-only public SDK producer; never installed as Knowledge orchestration."""

import argparse
import hashlib
import json
import os
from pathlib import Path

from amphora_contracts_artifacts import ContentDescriptor, DerivationDeclaration
from amphora_contracts_core import Scope
from amphora_tool_protocol import ArtifactClient, HttpTransport, ProtocolError, TransportLost, WorkerIdentity


class ObservedTransport:
    def __init__(self, endpoint, lose_ack):
        self.peer = HttpTransport(endpoint, os.environ["DATA_TOKEN"])
        self.lose_ack = lose_ack
        self.calls = []

    def request(self, method, path, body=None, **kwargs):
        self.calls.append((method, path))
        reply = self.peer.request(method, path, body, **kwargs)
        if self.lose_ack and method == "POST" and reply.status == 200:
            raise TransportLost("test_dropped_actual_committed_ack")
        return reply


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case", type=Path)
    parser.add_argument("mode", choices=["publish", "resume", "revoked"])
    args = parser.parse_args()
    case = json.loads(args.case.read_text(encoding="utf-8"))
    payload = json.dumps(case["result"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    content = ContentDescriptor.model_validate_json(json.dumps({"sha256": hashlib.sha256(payload).hexdigest(),
        "size_bytes": len(payload), "media_type": "application/json", "schema_ref": case["schema"]}))
    declaration = DerivationDeclaration.model_validate_json(json.dumps({"inputs": case["inputs"],
        "transformation": {"transformation_id": "knowledge.synthetic_logical_entailment", "version": "1",
                           "sha256": case["result"]["request"]["rule_set"]["sha256"]}}))
    transport = ObservedTransport(case["endpoint"], args.mode == "publish")
    client = ArtifactClient(transport, WorkerIdentity("fixture", Scope.model_validate(case["scope"])))

    def guard():
        assert args.mode == "publish", "Resume must be read-only after a committed publication"

    begun = client.begin_derived(content, declaration, "derive-initial", guard=guard, resume=args.mode != "publish")
    if args.mode == "publish":
        client.stream(begun.upload, payload, guard=guard)
    finalized = client.finalize(begun.upload, "derive-final", guard=guard, resume=args.mode != "publish")
    metadata = client.derivation(finalized.artifact)
    assert metadata.declaration == declaration and metadata.upload_id == begun.upload.upload_id
    assert metadata.origin.command_id == "derive-initial"
    if args.mode == "revoked":
        try:
            client.read(finalized.artifact)
        except ProtocolError:
            pass
        else:
            raise AssertionError("Revoked lineage allowed payload consumption")
        response = transport.request("GET", f"/v1/artifacts/{finalized.artifact.artifact_id}/content")
        assert response.status == 403 and json.loads(response.body)["reason_code"] == "rights_revoked"
    else:
        assert client.read(finalized.artifact) == payload
    if args.mode == "publish":
        assert [method for method, _ in transport.calls[:5]] == ["POST", "GET", "PUT", "POST", "GET"]
    else:
        assert all(method == "GET" for method, _ in transport.calls)
    print(json.dumps({"mode": args.mode, "artifact": finalized.artifact.model_dump(mode="json"),
        "derivation": metadata.model_dump(mode="json"), "calls": transport.calls}, sort_keys=True))


if __name__ == "__main__":
    main()
