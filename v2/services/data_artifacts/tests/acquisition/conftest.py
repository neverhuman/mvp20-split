import hashlib
import json
import uuid
from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_contracts_artifacts import parse_command
from amphora_contracts_core import ArtifactRef
from amphora_contracts_evidence import SourceRevision, prepared_schema
from amphora_data_artifacts.acquisition.ledger import AcquisitionLedger
from amphora_data_artifacts.acquisition.profiles import PreparedContentRule
from amphora_data_artifacts.acquisition.workflow import AcquisitionWorkflow
from amphora_data_artifacts.publication.model import ContentPolicy, UploadLimits
from amphora_data_artifacts.reads import ArtifactReads


@pytest.fixture
def ingestion(upload_env):
    e = upload_env
    profiles = [prepared_schema(kind) for kind in ("document", "lab")]
    e.uploads.policy = ContentPolicy(e.uploads.policy.allowed | frozenset(
        ("application/json", ref.schema_id, ref.version, ref.sha256) for ref in profiles),
        rules=(PreparedContentRule("document"), PreparedContentRule("lab")))
    e.uploads.limits = UploadLimits(max_bytes=65536, scope_bytes=1048576)
    principal = replace(e.principal, actions=frozenset({"read", "acquire", "source_history"}))
    ledger = AcquisitionLedger(e.engine)
    reads = ArtifactReads(e.engine, e.storage, 65536)

    def publish(content, schema=None):
        envelope = json.loads(e.raw(content))
        if schema is not None:
            envelope["payload"]["content"].update(media_type="application/json",
                                                 schema_ref=schema.model_dump(mode="json"))
        receipt = e.uploads.begin(e.principal, parse_command("artifacts.begin_upload", json.dumps(envelope)))
        response = e.client.put(f"/v1/uploads/{receipt.upload_id}/content", content=content, headers=e.headers)
        assert response.status_code == 200
        response = e.client.post("/v1/artifacts/finalize", headers=e.headers, json={
            "identity": {"command_family": "artifacts.finalize", "command_id": uuid.uuid4().hex,
                         "actor_id": "worker", "scope": principal.scope.model_dump()},
            "payload": {"upload_id": receipt.upload_id, "content": receipt.content.model_dump(mode="json")}})
        assert response.status_code == 200, response.text
        return ArtifactRef.model_validate_json(json.dumps(response.json()["artifact"]))

    def source(content=b"research notes", format="utf8_document"):
        return SourceRevision.model_validate_json(json.dumps({"wire_version": "1",
            "reference": {"scope": principal.scope.model_dump(), "source_id": "source", "revision_id": "r1",
                          "raw": publish(content).model_dump(mode="json")},
            "delivery": {"issuer_id": "fixture", "delivery_id": "d1"},
            "method": {"connector_id": "fixture", "connector_version": "1",
                       "configuration_sha256": hashlib.sha256(b"{}").hexdigest(), "format": format},
            "rights": {"scope": principal.scope.model_dump(), "rights_id": "fixture", "revision": 1},
            "supersedes": None, "completeness": "complete"}))

    return SimpleNamespace(workflow=AcquisitionWorkflow(reads, ledger), ledger=ledger, reads=reads,
                           principal=principal, publish=publish, source=source, env=e)


