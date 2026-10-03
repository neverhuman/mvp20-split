"""Actual installed Data/PG/Qdrant; retained restart and fresh-backend generation rebuild."""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest
from amphora_data_artifacts.retrieval.intents import GenerationIntents
from amphora_data_artifacts.retrieval.manifest import point_id
from amphora_data_artifacts.retrieval.proof_records import head
from amphora_data_artifacts.retrieval.publication import GenerationPublication
from amphora_data_artifacts.retrieval.qdrant.adapter import QdrantAdapter
from amphora_data_artifacts.retrieval.qdrant.configuration import QdrantConfiguration
from amphora_data_artifacts.retrieval.qdrant.transport import QdrantError

pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(
        os.environ.get("AMPHORA_TEST_QDRANT") != "1", reason="Explicit actual Qdrant fixture opt-in required"
    ),
]


def adapter(state):
    return QdrantAdapter(QdrantConfiguration(state["endpoint"], state["api_key"]))


def probe(e, state, lease, temporary):
    handoff = temporary / (lease.attempt.generation.generation_id + ".json")
    ref = lease.attempt.generation
    body = {
        "actor_id": e.p.actor_id,
        "scope": e.p.scope.model_dump(mode="json"),
        "actions": sorted(e.p.actions),
        "endpoint": state["endpoint"],
        "storage": str(e.ingestion.env.storage.root),
        "corpus_id": ref.corpus_id,
        "generation_id": ref.generation_id,
        "token": lease.attempt.token,
        "fence": lease.attempt.fence,
        "expires_at": lease.expires_at.isoformat(),
    }
    handoff.write_text(json.dumps(body), encoding="utf-8")
    environment = {
        name: os.environ[name] for name in ("PATH", "SYSTEMROOT", "TEMP", "TMP") if name in os.environ
    }
    environment.update(
        PYTHONUTF8="1",
        AMPHORA_REPLACEMENT_DATABASE_URL=e.engine.url.render_as_string(hide_password=False),
        AMPHORA_REPLACEMENT_API_KEY=state["api_key"],
    )
    python = os.environ.get("AMPHORA_TEST_QDRANT_PYTHON", sys.executable)
    command = [python, "-I", str(Path(__file__).absolute().with_name("replacement_probe.py")), str(handoff)]
    result = subprocess.run(
        command,
        cwd=temporary,
        env=environment,
        capture_output=True,
        text=True,
        timeout=45,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    assert result.returncode == 0, result.stderr[-3000:]
    return json.loads(result.stdout)


def test_installed_owner_reconstructs_retained_and_replacement_index(generation, tmp_path, monkeypatch):
    import qdrant_fixture as fixture

    e = generation
    primary = fixture.owned_state()
    backend = adapter(primary)
    intents = GenerationIntents(e.engine, backend.reference)
    publication = GenerationPublication(e.ingestion.reads, backend)
    intents.prepare(e.p, e.request)
    first = e.leases.claim(e.p, "corpus", "g1")
    proof = publication.build_and_verify(e.p, first)
    original = publication.publish(e.p, first)
    assert original.state == "published"
    original_bytes = original.model_dump_json()
    first_process = probe(e, primary, first, tmp_path)
    assert first_process["status"] == original.model_dump(mode="json")
    assert first_process["scores"] == [8.0]

    fixture.docker("restart", primary["container"])
    fixture.verify()
    primary = fixture.owned_state()
    restarted = probe(e, primary, first, tmp_path)
    assert restarted["pid"] != first_process["pid"]
    for field in ("status", "selected", "namespace", "projection_sha256", "scores"):
        assert restarted[field] == first_process[field]

    # A second owned backend lacks this namespace; preserve the original volume/history.
    with monkeypatch.context() as patch:
        patch.setattr(fixture, "STATE", fixture.ROOT / ".test-results/qdrant-replacement-fixture.json")
        if fixture.STATE.exists():
            fixture.resume()
        else:
            fixture.start()
        replacement = fixture.owned_state()
    new_backend = adapter(replacement)
    allowed = (point_id(e.binding),)
    query = (0.0, 2.0, 2.0) + (0.0,) * 13
    with pytest.raises(QdrantError, match="http_404"):
        new_backend.query(first.attempt.namespace, query, allowed)
    request = e.request.model_copy(
        update={"generation_id": "g2", "expected_head": original.generation.reference}
    )
    next_intents = GenerationIntents(e.engine, new_backend.reference)
    next_intents.prepare(e.p, request)
    second = e.leases.claim(e.p, "corpus", "g2")
    next_publication = GenerationPublication(e.ingestion.reads, new_backend)
    rebuilt_proof = next_publication.build_and_verify(e.p, second)
    rebuilt = next_publication.publish(e.p, second)
    assert rebuilt.generation.manifest == original.generation.manifest
    assert rebuilt_proof.projection_sha256 == proof.projection_sha256
    assert second.attempt.namespace != first.attempt.namespace
    assert rebuilt.generation.reference != original.generation.reference
    assert next_intents.read(e.p, "corpus", "g1").model_dump_json() == original_bytes
    assert next_publication.publish(e.p, first).model_dump_json() == original_bytes
    with e.engine.connect() as connection:
        assert head(connection, e.p, "corpus") == second.attempt.generation
    replacement_process = probe(e, replacement, second, tmp_path)
    assert replacement_process["scores"] == [8.0]
    assert replacement_process["status"] == rebuilt.model_dump(mode="json")
    with pytest.raises(QdrantError, match="http_404"):
        new_backend.query(first.attempt.namespace, query, allowed)

    evidence = {
        "timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "scope": e.p.scope.model_dump(mode="json"),
        "binding": e.binding.model_dump(mode="json"),
        "first_process": first_process,
        "retained_restart": restarted,
        "replacement_process": replacement_process,
        "original_history_unchanged": True,
        "old_pin_on_replacement": "unavailable_404_no_retargeting",
        "primary_container": primary["container"],
        "replacement_container": replacement["container"],
        "boundary": "Installed owner modules and actual PG/Qdrant; generation HTTP remains B2.04",
    }
    (fixture.ROOT / ".test-results/qdrant-generation-replacement.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
