"""Actual public-only source encoding and process replacement over an isolated installed owner."""

import hashlib
import json
import os
import struct
import sys
import uuid
from datetime import datetime
from pathlib import Path

import pytest

from .http_support import HttpOwner

pytestmark = pytest.mark.postgres
BASE = "/v1/representations"


def accepted(host, method, path, body=None):
    result = host.call(method, path, body)
    assert result.status == 200, (path, result.status, result.body)
    return result.json()


def command(scope, family, command_id, payload):
    return {
        "identity": {
            "command_family": family,
            "command_id": command_id,
            "actor_id": "worker",
            "scope": scope,
        },
        "payload": payload,
    }


def test_public_http_encoding_survives_owner_restart_and_preserves_rights(artifact_database, tmp_path):
    python = os.environ.get("AMPHORA_TEST_REPRESENTATION_PYTHON", sys.executable)
    scope = {"tenant_id": "representation-http", "project_id": uuid.uuid4().hex}
    storage = tmp_path / "bytes"
    storage.mkdir()
    example = json.loads((Path(__file__).parents[2] / "config.example.json").read_text(encoding="utf-8"))
    profile = example["profiles"][0]
    actions = [
        "upload",
        "finalize",
        "read",
        "acquire",
        "source_history",
        "manage_source_rights",
        "representation_manage",
        "representation_read",
        "representation_encode",
    ]
    config = {
        "database_url_env": "REP_HTTP_DATABASE",
        "storage_root": str(storage),
        "acquisition": True,
        "representations": True,
        "profiles": [profile],
        "limits": {"max_bytes": 65536, "scope_bytes": 1048576},
        "principals": [
            {"token_env": "REP_HTTP_TOKEN", "actor_id": "worker", "scope": scope, "actions": actions},
            {
                "token_env": "REP_OTHER_TOKEN",
                "actor_id": "worker",
                "scope": dict(scope, project_id="outside"),
                "actions": actions,
            },
        ],
    }
    config_path = tmp_path / "host.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    environment = dict(
        os.environ,
        REP_HTTP_DATABASE=artifact_database.render_as_string(hide_password=False),
        REP_HTTP_TOKEN="h" * 32,
        REP_OTHER_TOKEN="o" * 32,
    )
    source_bytes = b"prefix ABBA suffix"
    content = {
        "sha256": hashlib.sha256(source_bytes).hexdigest(),
        "size_bytes": len(source_bytes),
        "media_type": profile["media_type"],
        "schema_ref": {key: profile[key] for key in ("schema_id", "version", "sha256")},
    }
    host = HttpOwner(python, config_path, environment, "h" * 32)
    original_pid = host.process.pid
    try:
        upload = accepted(
            host,
            "POST",
            "/v1/uploads",
            command(scope, "artifacts.begin_upload", "source.begin", {"content": content}),
        )
        accepted(host, "PUT", "/v1/uploads/" + upload["upload_id"] + "/content", source_bytes)
        finalized = accepted(
            host,
            "POST",
            "/v1/artifacts/finalize",
            command(
                scope,
                "artifacts.finalize",
                "source.finalize",
                {"upload_id": upload["upload_id"], "content": content},
            ),
        )
        raw = finalized["artifact"]
        rights = {
            "wire_version": "1",
            "reference": {"scope": scope, "rights_id": "source", "revision": 1},
            "supersedes": None,
            "status": "granted",
            "allowed_uses": ["read", "process"],
            "expires_at": None,
            "retention": "retain_audit_payload",
        }
        accepted(host, "POST", "/v1/acquisition/rights", rights)
        source = {
            "wire_version": "1",
            "reference": {"scope": scope, "source_id": "source", "revision_id": "r1", "raw": raw},
            "delivery": {"issuer_id": "fixture", "delivery_id": "d1"},
            "method": {
                "connector_id": "fixture",
                "connector_version": "1",
                "configuration_sha256": hashlib.sha256(b"{}").hexdigest(),
                "format": "utf8_document",
            },
            "rights": rights["reference"],
            "supersedes": None,
            "completeness": "complete",
        }
        accepted(host, "POST", "/v1/acquisition/prepare", source)
        available = accepted(host, "GET", BASE + "/available-profiles")
        ref = accepted(host, "POST", BASE + "/profiles", available[0])
        request = {
            "wire_version": "1",
            "encoding_id": "original",
            "profile": ref,
            "source": {
                "source": source["reference"],
                "unit": "byte",
                "start": 7,
                "end": 11,
                "sha256": hashlib.sha256(b"ABBA").hexdigest(),
            },
        }
        original = accepted(host, "POST", BASE + "/encodings", request)
        assert original["outcome"]["state"] == "published"
        binding = original["outcome"]["binding"]
        vector_path = "/v1/artifacts/" + binding["vector"]["artifact_id"] + "/content"
        vector = accepted(host, "GET", vector_path)
        # Independently specified histogram for four ASCII bytes A,B,B,A.
        expected = struct.pack("<16f", 0, 2, 2, *([0] * 13))
        assert bytes.fromhex(vector["payload_hex"]) == expected
        assert vector["payload_sha256"] == hashlib.sha256(expected).hexdigest()
        assert vector["profile"] == ref
        binding_path = BASE + "/bindings/" + binding["reference"]["binding_id"]
        assert accepted(host, "GET", binding_path) == binding
        assert host.call("GET", binding_path, token="o" * 32).status == 404
    finally:
        host.close()
    replacement = HttpOwner(python, config_path, environment, "h" * 32)
    try:
        assert accepted(replacement, "GET", BASE + "/encodings/original") == original
        assert accepted(replacement, "POST", BASE + "/encodings", request) == original
        assert accepted(replacement, "GET", vector_path) == vector
        alias = dict(request, encoding_id="alias")
        assert accepted(replacement, "POST", BASE + "/encodings", alias)["outcome"]["binding"] == binding
        denied = dict(
            rights,
            reference=dict(rights["reference"], revision=2),
            supersedes=rights["reference"],
            status="revoked",
            allowed_uses=[],
        )
        accepted(replacement, "POST", "/v1/acquisition/rights", denied)
        assert replacement.call("GET", binding_path).status == 403
        assert replacement.call("GET", vector_path).status == 403
        assert accepted(replacement, "GET", BASE + "/encodings/original") == original
        assert accepted(replacement, "POST", BASE + "/encodings", request) == original
        assert (
            replacement.call("POST", BASE + "/encodings", dict(request, encoding_id="revoked-alias")).status
            == 403
        )
        evidence = {
            "timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scope": scope,
            "original_pid": original_pid,
            "replacement_pid": replacement.process.pid,
            "profile": ref,
            "source": source["reference"],
            "binding": binding,
            "oracle": "ABBA: finite binary32 counts2 in bins1 and2, all other bins0",
            "statuses": {
                "published": 200,
                "replacement_exact_replay": 200,
                "wrong_scope": 404,
                "revoked_binding": 403,
                "revoked_content": 403,
                "revoked_new_alias": 403,
                "historical_replay": 200,
            },
        }
        folder = Path(__file__).absolute().parents[4] / ".test-results" / "representation-http"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "replacement.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    finally:
        replacement.close()
