"""Actual backend effects plus injected response uncertainty at the owner boundary."""

import json
import os
from datetime import datetime
from pathlib import Path

import pytest
from amphora_data_artifacts.retrieval.intents import GenerationIntents
from amphora_data_artifacts.retrieval.publication import GenerationPublication
from amphora_data_artifacts.retrieval.qdrant.adapter import QdrantAdapter
from amphora_data_artifacts.retrieval.qdrant.configuration import QdrantConfiguration
from amphora_data_artifacts.retrieval.qdrant.transport import QdrantError
from amphora_data_artifacts.retrieval.service import RetrievalService

from ..processes.test_death_replay import expire
from ..test_generation_publication import rows

pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(os.environ.get("AMPHORA_TEST_QDRANT") != "1", reason="Actual Qdrant required"),
]


@pytest.mark.parametrize("error", ["qdrant_http_409", "qdrant_http_500"])
def test_uncertain_effect_has_no_authority_and_fresh_attempt_preserves_orphan(generation, monkeypatch, error):
    from qdrant_fixture import owned_state

    e = generation
    state = owned_state()
    backend = QdrantAdapter(QdrantConfiguration(state["endpoint"], state["api_key"]))
    intents = GenerationIntents(e.engine, backend.reference)
    intents.prepare(e.p, e.request)
    old = e.leases.claim(e.p, "corpus", "g1")
    build = backend.build

    def uncertain(namespace, snapshot):
        build(namespace, snapshot)
        raise QdrantError(error)

    monkeypatch.setattr(backend, "build", uncertain)
    with pytest.raises(QdrantError, match=error):
        GenerationPublication(e.ingestion.reads, backend).build_and_verify(e.p, old)
    assert rows(e, "index_verifications") == rows(e, "index_publications") == rows(e, "index_heads") == 0
    orphan = backend.inspect(old.attempt.namespace)
    assert len(orphan.points) == 1
    # A live lease remains busy; no hidden retry or premature publication follows an error.
    service = RetrievalService(e.ingestion.reads, backend)
    assert service.advance(e.p, e.request).state == "building"
    monkeypatch.setattr(backend, "build", build)
    expire(e)
    fresh = e.leases.claim(e.p, "corpus", "g1")
    assert fresh.attempt.fence == old.attempt.fence + 1
    assert fresh.attempt.namespace != old.attempt.namespace
    publication = GenerationPublication(e.ingestion.reads, backend)
    proof = publication.build_and_verify(e.p, fresh)
    result = publication.publish(e.p, fresh)
    assert result.state == "published"
    assert backend.inspect(old.attempt.namespace) == orphan
    assert backend.inspect(fresh.attempt.namespace) == orphan
    assert rows(e, "index_build_attempts") == 2
    assert rows(e, "index_verifications") == rows(e, "index_publications") == rows(e, "index_heads") == 1
    assert service.advance(e.p, e.request) == result
    folder = Path(__file__).absolute().parents[5] / ".test-results/retrieval-uncertainty"
    folder.mkdir(exist_ok=True)
    evidence = {
        "timestamp_local": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S"),
        "scope": e.p.scope.model_dump(mode="json"),
        "injected_error_after_actual_write": error,
        "old_attempt": {
            "generation": old.attempt.generation.descriptor(),
            "namespace": old.attempt.namespace,
            "fence": old.attempt.fence,
            "token": old.attempt.token,
        },
        "verified": proof.descriptor(),
        "published": result.model_dump(mode="json"),
        "orphan_retained": True,
        "claim": "Owner recovery under injected response uncertainty; actual Qdrant effects, no induced server fault claim",
    }
    (folder / (error + ".json")).write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
