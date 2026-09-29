"""Synthetic external issuer: HTTP-only publication and receipt submission; no owner imports/SQL."""

import hashlib
import json
import os
import sys
import uuid
from pathlib import Path
from urllib.request import ProxyHandler, Request, build_opener


def main():
    assert not any("DATABASE_URL" in key for key in os.environ)
    job = json.loads(Path(sys.argv[1]).read_bytes())
    token = os.environ["ISSUER_TOKEN"]

    def call(endpoint, path, value=None, method=None):
        body = value if isinstance(value, bytes) else json.dumps(value).encode() if value is not None else None
        request = Request(endpoint + path, body, method=method,
            headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
        with build_opener(ProxyHandler({})).open(request, timeout=15) as response:
            return json.loads(response.read())

    def command(family, payload):
        return {"identity": {"scope": job["scope"], "actor_id": "worker1", "command_family": family,
            "command_id": uuid.uuid4().hex}, "payload": payload}

    observed = call(job["runtime"], job["wait_path"])
    expected = observed["expectation"]
    output = None
    if job["status"] == "accepted":
        body = json.dumps(job["output"]).encode()
        content = {"sha256": hashlib.sha256(body).hexdigest(), "size_bytes": len(body),
            "media_type": "application/json", "schema_ref": expected["output_type"]["schema_ref"]}
        uploaded = call(job["artifact"], "/v1/uploads", command("artifacts.begin_upload", {"content": content}))
        call(job["artifact"], "/v1/uploads/" + uploaded["upload_id"] + "/content", body, "PUT")
        output = call(job["artifact"], "/v1/artifacts/finalize",
            command("artifacts.finalize", {"upload_id": uploaded["upload_id"], "content": content}))["artifact"]
        outcome = {"status": "accepted", "output": {"kind": "artifact", "artifact": output,
            "representation": expected["output_type"]["representation"], "unit": expected["output_type"]["unit"]}}
    elif job["status"] == "superseded":
        outcome = {"status": "superseded", "replacement_revision": "later", "reason_code": "fixture_superseded"}
    else:
        outcome = {"status": job["status"], "reason_code": "fixture_evidence_unavailable"}
    receipt = {"schema_version": "1", "issuer_id": "worker1", "receipt_id": uuid.uuid4().hex, "scope": job["scope"],
        "purpose": job.get("purpose", expected["purpose"]), "revision": expected["expected_revision"],
        "subject": expected["subject"], "outcome": outcome}
    submission = command("graph.submit_receipt", {"run_id": expected["run_id"], "activation_id": expected["activation_id"],
        "wait_revision": expected["wait_revision"], "expectation_sha256": observed["expectation_sha256"], "receipt": receipt})
    reply = call(job["runtime"], "/v1/graph-receipts", submission)
    print(json.dumps({"command": submission, "reply": reply, "artifact": output, "issuer_process": os.getpid()}))


if __name__ == "__main__":
    main()
