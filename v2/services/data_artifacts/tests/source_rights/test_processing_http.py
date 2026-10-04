"""Actual installed Data HTTP source-rights boundary, with process replacement."""

import hashlib
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

import pytest

from ..representations.http_support import HttpOwner
from ..representations.test_http_replacement import accepted, command

pytestmark = pytest.mark.postgres


def test_processing_content_preserves_rights_across_owner_replacement(artifact_database, tmp_path):
    python = os.environ.get("AMPHORA_TEST_PROCESSING_CONTENT_PYTHON", sys.executable)
    scope = {"tenant_id": "processing-content-http", "project_id": uuid.uuid4().hex}
    storage = tmp_path / "bytes"
    storage.mkdir()
    profile = json.loads((Path(__file__).parents[2] / "config.example.json").read_bytes())["profiles"][0]
    actions = ["upload", "finalize", "read", "acquire", "source_history", "manage_source_rights"]
    config = {"database_url_env": "PROCESS_HTTP_DATABASE", "storage_root": str(storage), "acquisition": True,
              "profiles": [profile], "limits": {"max_bytes": 65536, "scope_bytes": 1048576},
              "principals": [{"token_env": "PROCESS_HTTP_TOKEN", "actor_id": "worker",
                              "scope": scope, "actions": actions}]}
    config_path = tmp_path / "host.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    environment = dict(os.environ, PROCESS_HTTP_DATABASE=artifact_database.render_as_string(hide_password=False),
                       PROCESS_HTTP_TOKEN="p" * 32)
    payload = b"synthetic process-authorized document"
    descriptor = {"sha256": hashlib.sha256(payload).hexdigest(), "size_bytes": len(payload),
                  "media_type": profile["media_type"],
                  "schema_ref": {key: profile[key] for key in ("schema_id", "version", "sha256")}}
    host = HttpOwner(python, config_path, environment, "p" * 32)
    first_pid = host.process.pid
    try:
        upload = accepted(host, "POST", "/v1/uploads",
                          command(scope, "artifacts.begin_upload", "begin", {"content": descriptor}))
        accepted(host, "PUT", "/v1/uploads/" + upload["upload_id"] + "/content", payload)
        artifact = accepted(host, "POST", "/v1/artifacts/finalize", command(scope, "artifacts.finalize", "finalize",
            {"upload_id": upload["upload_id"], "content": descriptor}))["artifact"]
        rights = {"wire_version": "1", "reference": {"scope": scope, "rights_id": "source", "revision": 1},
                  "supersedes": None, "status": "granted", "allowed_uses": ["read", "process"],
                  "expires_at": None, "retention": "retain_audit_payload"}
        accepted(host, "POST", "/v1/acquisition/rights", rights)
        source = {"wire_version": "1", "reference": {"scope": scope, "source_id": "source",
                  "revision_id": "r1", "raw": artifact}, "delivery": {"issuer_id": "fixture", "delivery_id": "d1"},
                  "method": {"connector_id": "fixture", "connector_version": "1",
                             "configuration_sha256": hashlib.sha256(b"{}").hexdigest(), "format": "utf8_document"},
                  "rights": rights["reference"], "supersedes": None, "completeness": "complete"}
        accepted(host, "POST", "/v1/acquisition/prepare", source)
        route = f"/v1/artifacts/{artifact['artifact_id']}"
        first = host.call("GET", route + "/processing-content")
        assert first.status == 200 and first.body == payload
        readonly = dict(rights, reference=dict(rights["reference"], revision=2),
                        supersedes=rights["reference"], allowed_uses=["read"])
        accepted(host, "POST", "/v1/acquisition/rights", readonly)
        assert host.call("GET", route + "/content").body == payload
        assert host.call("GET", route + "/processing-content").status == 403
    finally:
        host.close()
    replacement = HttpOwner(python, config_path, environment, "p" * 32)
    try:
        assert replacement.process.pid != first_pid
        assert replacement.call("GET", route + "/processing-content").status == 403
        assert replacement.call("GET", route + "/content").body == payload
        assert accepted(replacement, "GET", "/v1/acquisition/sources/source/r1") == source
        third = dict(rights, reference=dict(rights["reference"], revision=3), supersedes=readonly["reference"])
        accepted(replacement, "POST", "/v1/acquisition/rights", third)
        allowed = replacement.call("GET", route + "/processing-content")
        assert allowed.status == 200 and allowed.body == payload
        evidence = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "passed",
                    "source": source["reference"], "rights": ["process_allowed", "read_only", "process_allowed"],
                    "processes": [first_pid, replacement.process.pid], "source_history_unchanged": True,
                    "limitations": ["Current read fence is not continuing permission or provider egress authority"]}
        destination = Path(os.environ.get("AMPHORA_PROCESSING_CONTENT_EVIDENCE", str(tmp_path / "evidence.json")))
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    finally:
        replacement.close()
