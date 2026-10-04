"""Public-only installed CLI HTTP with actual source, index and query reconstruction."""

import hashlib
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

import pytest

from ..representations.http_support import HttpOwner
from ..representations.test_http_replacement import accepted, command

pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(
        os.environ.get("AMPHORA_TEST_QDRANT") != "1", reason="Explicit actual Qdrant fixture required"
    ),
]
REP = "/v1/representations"
BASE = "/v1/retrieval"


def source_over_http(host, scope, profile):
    content = {
        "sha256": hashlib.sha256(b"ABBA").hexdigest(),
        "size_bytes": 4,
        "media_type": profile["media_type"],
        "schema_ref": {k: profile[k] for k in ("schema_id", "version", "sha256")},
    }
    upload = accepted(
        host,
        "POST",
        "/v1/uploads",
        command(scope, "artifacts.begin_upload", "source.begin", {"content": content}),
    )
    accepted(host, "PUT", "/v1/uploads/" + upload["upload_id"] + "/content", b"ABBA")
    raw = accepted(
        host,
        "POST",
        "/v1/artifacts/finalize",
        command(
            scope,
            "artifacts.finalize",
            "source.finalize",
            {"upload_id": upload["upload_id"], "content": content},
        ),
    )["artifact"]
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
        "delivery": {"issuer_id": "fixture", "delivery_id": "source-delivery"},
        "method": {
            "connector_id": "fixture",
            "connector_version": "1",
            "configuration_sha256": hashlib.sha256(b"{}").hexdigest(),
            "format": "utf8_document",
        },
        "rights": rights["reference"],
        "supersedes": None,
        "completeness": "unknown",
    }
    accepted(host, "POST", "/v1/acquisition/prepare", source)
    return source, rights


def encode_over_http(host, profile, source, encoding_id):
    ref = accepted(host, "POST", REP + "/profiles", profile)
    request = {
        "wire_version": "1",
        "encoding_id": encoding_id,
        "profile": ref,
        "source": {
            "source": source["reference"],
            "unit": "byte",
            "start": 0,
            "end": 4,
            "sha256": source["reference"]["raw"]["sha256"],
        },
    }
    return accepted(host, "POST", REP + "/encodings", request)["outcome"]["binding"]


def generation_request(binding, generation_id, expected_head):
    return {
        "wire_version": "1",
        "corpus_id": "corpus",
        "generation_id": generation_id,
        "profile": binding["profile"],
        "bindings": [binding["reference"]],
        "expected_head": expected_head,
    }


def query_request(binding, generation, retrieval_id):
    return {
        "wire_version": "1",
        "retrieval_id": retrieval_id,
        "generation": generation,
        "query": binding["reference"],
        "policy": {
            "format": "data.exact-dot-ranking.v1",
            "top_k": 1,
            "bindings": None,
            "metric": "dot",
            "order": "score_desc_binding_asc",
            "quality_filter": "none",
        },
    }


def test_installed_public_http_retains_generation_query_pins_across_owner_and_backend_replacement(
    artifact_database, tmp_path, monkeypatch
):
    import qdrant_fixture as fixture

    python = os.environ.get("AMPHORA_TEST_RETRIEVAL_HTTP_PYTHON", sys.executable)
    check = 'import importlib.util; assert all(importlib.util.find_spec(m) is None for m in ("amphora_research","amphora_knowledge","amphora_campaign_runtime"))'
    subprocess.run(
        [python, "-I", "-c", check],
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    primary = fixture.owned_state()
    with monkeypatch.context() as patch:
        patch.setattr(fixture, "STATE", fixture.ROOT / ".test-results/qdrant-replacement-fixture.json")
        fixture.resume() if fixture.STATE.exists() else fixture.start()
        replacement = fixture.owned_state()
    scope = {"tenant_id": "retrieval-http", "project_id": uuid.uuid4().hex}
    example = json.loads((Path(__file__).parents[2] / "config.example.json").read_text(encoding="utf-8"))
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
        "database_url_env": "RETRIEVAL_HTTP_DATABASE",
        "storage_root": str(tmp_path / "bytes"),
        "acquisition": True,
        "representations": True,
        "profiles": example["profiles"],
        "limits": {"max_bytes": 65536, "scope_bytes": 1048576},
        "retrieval": {"endpoint": primary["endpoint"], "token_env": "RETRIEVAL_HTTP_QDRANT"},
        "principals": [
            {"token_env": "RETRIEVAL_HTTP_TOKEN", "actor_id": "worker", "scope": scope, "actions": actions},
            {
                "token_env": "RETRIEVAL_HTTP_OTHER",
                "actor_id": "worker",
                "scope": dict(scope, project_id="outside"),
                "actions": actions,
            },
        ],
    }
    config_path = tmp_path / "host.json"
    (tmp_path / "bytes").mkdir()
    config_path.write_text(json.dumps(config), encoding="utf-8")
    environment = {
        name: os.environ[name] for name in ("PATH", "SYSTEMROOT", "TEMP", "TMP") if name in os.environ
    }
    environment.update(
        PYTHONUTF8="1",
        RETRIEVAL_HTTP_DATABASE=artifact_database.render_as_string(hide_password=False),
        RETRIEVAL_HTTP_TOKEN="h" * 32,
        RETRIEVAL_HTTP_OTHER="o" * 32,
        RETRIEVAL_HTTP_QDRANT=primary["api_key"],
    )
    host = HttpOwner(python, config_path, environment, "h" * 32)
    processes = [host.process.pid]
    try:
        source, rights = source_over_http(host, scope, example["profiles"][0])
        profiles = accepted(host, "GET", REP + "/available-profiles")
        assert [(p["version"], p["space"]["normalization"]) for p in profiles] == [("1", "none"), ("2", "l2")]
        old_binding = encode_over_http(host, profiles[0], source, "old")
        old_request = generation_request(old_binding, "g1", None)
        old = accepted(host, "POST", BASE + "/generations", old_request)
        assert old["state"] == "published"
        old_query = query_request(old_binding, old["generation"]["reference"], "q1")
        original = accepted(host, "POST", BASE + "/queries", old_query)
        assert original["matches"] == [{"binding": old_binding, "score": 8.0}]
        # Unknown completeness stays usable; no quality threshold or promotion is invented.
        new_binding = encode_over_http(host, profiles[1], source, "new")
        new = accepted(
            host,
            "POST",
            BASE + "/generations",
            generation_request(new_binding, "g2", old["generation"]["reference"]),
        )
        new_query = query_request(new_binding, new["generation"]["reference"], "q2")
        normalized = accepted(host, "POST", BASE + "/queries", new_query)
        assert normalized["matches"][0]["score"] == pytest.approx(1.0, abs=1e-6)
        cross = dict(new_query, retrieval_id="cross", query=old_binding["reference"])
        assert host.call("POST", BASE + "/queries", cross).status == 409
        assert host.call("GET", BASE + "/queries/q1", token="o" * 32).status == 404
        old_route = BASE + "/generations/corpus/g1?sha256=" + old["generation"]["reference"]["sha256"]
        assert accepted(host, "GET", old_route) == old
        host.close()

        # Same owner/database/bytes, fresh process, missing projection on a second actual backend.
        config["retrieval"]["endpoint"] = replacement["endpoint"]
        config_path.write_text(json.dumps(config), encoding="utf-8")
        environment["RETRIEVAL_HTTP_QDRANT"] = replacement["api_key"]
        host = HttpOwner(python, config_path, environment, "h" * 32)
        processes.append(host.process.pid)
        assert accepted(host, "GET", BASE + "/queries/q1") == original
        assert accepted(host, "GET", BASE + "/queries/q2") == normalized
        assert accepted(host, "POST", BASE + "/queries", old_query) == original
        assert accepted(host, "GET", old_route) == old
        missing = dict(old_query, retrieval_id="missing-projection")
        unavailable = host.call("POST", BASE + "/queries", missing)
        assert unavailable.status == 503 and unavailable.json()["detail"] == "qdrant_http_404"
        assert host.call("GET", BASE + "/queries/missing-projection").status == 409
        host.close()

        config["retrieval"]["endpoint"] = primary["endpoint"]
        config_path.write_text(json.dumps(config), encoding="utf-8")
        environment["RETRIEVAL_HTTP_QDRANT"] = primary["api_key"]
        host = HttpOwner(python, config_path, environment, "h" * 32)
        processes.append(host.process.pid)
        recovered = accepted(host, "POST", BASE + "/queries", missing)
        assert recovered["matches"] == original["matches"]
        assert accepted(host, "GET", BASE + "/queries/q2") == normalized
        denied = dict(
            rights,
            reference=dict(rights["reference"], revision=2),
            supersedes=rights["reference"],
            status="revoked",
            allowed_uses=[],
        )
        accepted(host, "POST", "/v1/acquisition/rights", denied)
        for path in ("/queries/q1", "/queries/q2", "/queries/missing-projection"):
            result = host.call("GET", BASE + path)
            assert result.status == 403 and result.json()["detail"] == "rights_revoked"
        assert (
            host.call("POST", BASE + "/queries", dict(old_query, retrieval_id="revoked-query")).status == 403
        )
        # Existing generation status is historical metadata under its original actor contract.
        assert accepted(host, "GET", old_route) == old
        # Restore read/process authority with an explicit new revision to verify unchanged records.
        restored = dict(
            rights, reference=dict(rights["reference"], revision=3), supersedes=denied["reference"]
        )
        accepted(host, "POST", "/v1/acquisition/rights", restored)
        assert accepted(host, "GET", BASE + "/queries/q1") == original
        assert accepted(host, "GET", BASE + "/queries/q2") == normalized
        assert len(set(processes)) == 3
        evidence = {
            "timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "processes": processes,
            "scope": scope,
            "old_generation": old,
            "new_generation": new,
            "original": original,
            "normalized": normalized,
            "recovered": recovered,
            "unavailable_status": unavailable.status,
            "revoked_status": 403,
            "restored_original_unchanged": True,
            "private_peers_absent": True,
            "operations": "Public HTTP only after fixture setup",
        }
        (Path(__file__).absolute().parents[4] / ".test-results/retrieval-http-replacement.json").write_text(
            json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
        )
    finally:
        host.close()
