"""Actual PostgreSQL/Qdrant adversaries beyond the inherited boundary oracles."""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from threading import Barrier

import pytest
from amphora_data_artifacts.retrieval.mapping import reference_to_wire
from amphora_data_artifacts.retrieval.proof_records import head, publication
from amphora_data_artifacts.retrieval.qdrant.adapter import QdrantAdapter
from amphora_data_artifacts.retrieval.qdrant.collections import path
from amphora_data_artifacts.retrieval.qdrant.configuration import QdrantConfiguration
from amphora_data_artifacts.retrieval.qdrant.points import encode
from amphora_data_artifacts.retrieval.records import key_for, load_plan
from amphora_data_artifacts.retrieval.service import RetrievalService
from amphora_data_artifacts.retrieval.validation import RetrievalError
from amphora_data_artifacts.source_rights.ledger import SourceRights
from sqlalchemy import text

from ..queries.test_broker import query as query
from ..test_generation_publication import rows

pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(
        os.environ.get("AMPHORA_TEST_QDRANT") != "1", reason="Explicit actual Qdrant fixture required"
    ),
]


def backend():
    from qdrant_fixture import owned_state

    state = owned_state()
    return QdrantAdapter(QdrantConfiguration(state["endpoint"], state["api_key"]))


def evidence(name, e, details):
    folder = Path(__file__).absolute().parents[5] / ".test-results/retrieval-adversaries"
    folder.mkdir(exist_ok=True)
    value = {"timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "scope": e.p.scope.model_dump(mode="json"), "source": e.source.reference.model_dump(mode="json"),
        "details": details}
    (folder / (name + ".json")).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


@pytest.fixture
def actual(query):
    e = query
    e.actual_backend = backend()
    e.service = RetrievalService(e.ingestion.reads, e.actual_backend)
    e.actual_request = e.request.model_copy(
        update={"corpus_id": "actual", "generation_id": "g1", "bindings": (e.binding.reference,)}
    )
    e.actual_status = e.service.advance(e.p, e.actual_request)
    e.actual_query = e.query_request.model_copy(update={"generation": e.actual_status.generation.reference})
    return e


def test_rights_expiry_without_revision_change_discards_actual_query_observation(actual, monkeypatch):
    e = actual
    rights = SourceRights(e.engine)
    prior = rights.history(e.p, e.source.rights.rights_id, 1)
    with e.engine.connect() as c:
        deadline = c.execute(text("SELECT clock_timestamp()")).scalar_one() + timedelta(seconds=3)
    expires = prior.model_copy(
        update={
            "reference": prior.reference.model_copy(update={"revision": 2}),
            "supersedes": prior.reference,
            "expires_at": deadline,
        }
    )
    rights.publish(e.p, expires)
    original = e.actual_backend.query
    seen = []

    def delayed(*args):
        result = original(*args)
        seen.extend(result)
        with e.engine.connect() as c:
            remaining = (deadline - c.execute(text("SELECT clock_timestamp()")).scalar_one()).total_seconds()
        time.sleep(max(0, remaining) + 0.05)
        return result

    monkeypatch.setattr(e.actual_backend, "query", delayed)
    with pytest.raises(RetrievalError, match="rights_changed"):
        e.service.queries.retrieve(e.p, e.actual_query)
    assert len(seen) == 1 and seen[0].score == 8.0
    assert rows(e, "retrieval_queries") == 1 and rows(e, "retrieval_results") == 0
    assert rights.history(e.p, e.source.rights.rights_id, 2) == expires
    assert e.service.queries.retrieve(e.p, e.actual_query).matches == ()
    assert len(seen) == 1  # No second backend call for an empty authorized set.
    evidence("expiry", e, {"generation": e.actual_status.generation.reference.model_dump(mode="json"),
        "expired_policy": expires.model_dump(mode="json"), "observed_score": seen[0].score,
        "first_result_count": 0, "retry_matches": [], "head_revision_unchanged": True})


def test_corrupt_selected_vector_is_operational_failure_and_fresh_generation_repairs(actual):
    e = actual
    with e.engine.connect() as c:
        plan = load_plan(c, e.p, "actual", "g1")
        proof = publication(c, key_for(e.p, "actual", "g1"), plan)
    snapshot = e.actual_backend.inspect(proof.attempt.namespace)
    point = encode(snapshot.points[0], snapshot.dimensions)
    point["vector"] = [0.0] * 16
    # Adversarial fixture corruption; never restore the selected namespace in place.
    e.actual_backend.transport.request(
        "PUT", path(proof.attempt.namespace) + "/points?wait=true", {"points": [point]}
    )
    with pytest.raises(RetrievalError, match="query_content"):
        e.service.queries.retrieve(e.p, e.actual_query)
    assert rows(e, "retrieval_queries") == 1 and rows(e, "retrieval_results") == 0
    repaired = e.service.advance(
        e.p,
        e.actual_request.model_copy(
            update={"generation_id": "g2", "expected_head": e.actual_status.generation.reference}
        ),
    )
    request = e.actual_query.model_copy(
        update={"retrieval_id": "repaired", "generation": repaired.generation.reference}
    )
    assert e.service.queries.retrieve(e.p, request).matches[0].score == 8.0
    assert (
        e.service.generation(e.p, "actual", "g1", e.actual_status.generation.reference.sha256)
        == e.actual_status
    )
    with pytest.raises(RetrievalError, match="query_content"):
        e.service.queries.retrieve(e.p, e.actual_query)
    assert rows(e, "retrieval_results") == 1
    evidence("corruption", e, {"original": e.actual_status.generation.reference.model_dump(mode="json"),
        "repaired": repaired.generation.reference.model_dump(mode="json"), "original_namespace": proof.attempt.namespace,
        "original_pin_still_fails": True, "repaired_score": 8.0, "original_history_unchanged": True})


def test_actual_verified_publishers_have_one_compare_and_set_winner(generation):
    e = generation
    service = RetrievalService(e.ingestion.reads, backend())
    leases = []
    for name in ("left", "right"):
        service.intents.prepare(e.p, e.request.model_copy(update={"generation_id": name}))
        leases.append(service.leases.claim(e.p, "corpus", name))
    barrier = Barrier(2, timeout=15)

    def publish(lease):
        service.publication.build_and_verify(e.p, lease)
        barrier.wait()
        try:
            return service.publication.publish(e.p, lease)
        except RetrievalError as error:
            assert str(error) == "retrieval_head_conflict"
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(publish, leases))
    assert sum(value is not None for value in results) == 1
    winner = next(value for value in results if value is not None)
    assert rows(e, "index_verifications") == 2 and rows(e, "index_publications") == 1
    with e.engine.connect() as c:
        assert reference_to_wire(head(c, e.p, "corpus")) == winner.generation.reference
    loser = leases[results.index(None)]
    assert service.intents.read(e.p, "corpus", loser.attempt.generation.generation_id).state == "verified"
    assert service.publication.publish(e.p, leases[results.index(winner)]) == winner
    evidence("competing_publishers", e, {"winner": winner.generation.reference.model_dump(mode="json"),
        "loser": loser.attempt.generation.descriptor(), "verified_count": 2, "published_count": 1})
