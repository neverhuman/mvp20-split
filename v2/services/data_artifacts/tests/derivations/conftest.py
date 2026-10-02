import json
import uuid
from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_contracts_artifacts import DerivedUploadReceipt
from amphora_data_artifacts.access import Credentials
from amphora_data_artifacts.api import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def derived_env(ingestion):
    e = ingestion
    principal = replace(e.principal, actions=e.principal.actions | {"upload", "finalize"})
    credentials = Credentials([("d" * 32, principal)])
    with TestClient(create_app(e.env.uploads, e.env.storage, credentials)) as client:
        headers = {"Authorization": "Bearer " + "d" * 32}

        def begin(inputs, payload=b"derived", command_id=None):
            raw = json.loads(e.env.raw(payload, command_id))
            raw["identity"]["command_family"] = "artifacts.begin_derived_upload"
            raw["payload"]["declaration"] = {
                "transformation": {"transformation_id": "synthetic.method", "version": "1", "sha256": "c" * 64},
                "inputs": [ref.model_dump(mode="json") for ref in inputs]}
            return raw

        def stream(raw, payload=b"derived"):
            response = client.post("/v1/derived-uploads", json=raw, headers=headers)
            assert response.status_code == 200, response.text
            receipt = DerivedUploadReceipt.model_validate_json(response.content)
            response = client.put(f"/v1/uploads/{receipt.upload.upload_id}/content", content=payload, headers=headers)
            assert response.status_code == 200, response.text
            return {"identity": {**raw["identity"], "command_family": "artifacts.finalize", "command_id": uuid.uuid4().hex},
                    "payload": {"upload_id": receipt.upload.upload_id, "content": receipt.upload.content.model_dump(mode="json")}}

        def revoke(source, *, status="revoked", uses=(), expires_at=None):
            ref = source.rights
            prior = e.workflow.rights.history(e.principal, ref.rights_id, ref.revision)
            updated = prior.model_copy(update={"reference": ref.model_copy(update={"revision": ref.revision + 1}),
                "supersedes": ref, "status": status, "allowed_uses": uses, "expires_at": expires_at})
            e.workflow.rights.publish(replace(principal, actions=frozenset({"manage_source_rights"})), updated)

        def linked_source():
            source = e.source()
            prepared = e.workflow.prepare(e.principal, source)
            output = e.publish(prepared.content, prepared.output_schema)
            e.workflow.retain(e.principal, source, "trace", output)
            return source, output

        yield SimpleNamespace(e=e, client=client, headers=headers, principal=principal,
                              begin=begin, stream=stream, revoke=revoke, linked_source=linked_source)
