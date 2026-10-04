"""Eight actual installed HTTP process-death points with PostgreSQL/Qdrant recovery."""

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import pytest
from amphora_contracts_representations import RetrieveRepresentations
from amphora_data_artifacts.retrieval.qdrant.adapter import QdrantAdapter
from amphora_data_artifacts.retrieval.qdrant.configuration import QdrantConfiguration
from amphora_data_artifacts.retrieval.queries.mapping import policy_to_wire
from amphora_data_artifacts.retrieval.queries.policy import QueryPolicy
from amphora_data_artifacts.retrieval.service import RetrievalService
from sqlalchemy import text

from ...representations.http_support import HttpOwner
from ...representations.test_http_replacement import accepted
from ..test_generation_publication import rows
from .support import FaultOwner, configuration

STAGES = (
    "generation_intent",
    "projection_written",
    "verification_committed",
    "publication_committed",
    "query_intent",
    "query_observed",
    "query_before_result",
    "query_committed",
)
pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(
        os.environ.get("AMPHORA_TEST_QDRANT") != "1", reason="Explicit actual Qdrant fixture required"
    ),
]


def cursor(e):
    with e.engine.connect() as c:
        return dict(
            c.execute(
                text(
                    "SELECT phase,token,fence FROM artifacts.index_generation_cursors "
                    "WHERE tenant_id=:tenant AND project_id=:project AND corpus_id='corpus' AND generation_id='g1'"
                ),
                e.p.bindings,
            )
            .mappings()
            .one()
        )


def expire(e):
    with e.engine.begin() as c:
        c.execute(
            text(
                "UPDATE artifacts.index_generation_cursors SET expires_at=clock_timestamp()-interval '1 second' "
                "WHERE tenant_id=:tenant AND project_id=:project AND corpus_id='corpus' AND generation_id='g1'"
            ),
            e.p.bindings,
        )


@pytest.mark.parametrize("stage", STAGES)
def test_process_death_replays_only_committed_authority(generation, tmp_path, stage):
    from qdrant_fixture import owned_state

    e = generation
    state = owned_state()
    python = os.environ.get("AMPHORA_TEST_RETRIEVAL_PROCESS_PYTHON", sys.executable)
    service = RetrievalService(
        e.ingestion.reads, QdrantAdapter(QdrantConfiguration(state["endpoint"], state["api_key"]))
    )
    query = stage.startswith("query_")
    if query:
        status = service.advance(e.p, e.request)
        request = RetrieveRepresentations(
            wire_version="1",
            retrieval_id="interrupted",
            generation=status.generation.reference,
            query=e.binding.reference,
            policy=policy_to_wire(QueryPolicy(1)),
        )
        route = "/v1/retrieval/queries"
    else:
        request = e.request
        route = "/v1/retrieval/generations"
    config, environment = configuration(e, state, tmp_path)
    host = FaultOwner(python, config, environment, stage)
    original_pid = host.process.pid
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            response = pool.submit(host.call, "POST", route, request.model_dump(mode="json"))
            reached = host.events.get(timeout=15)
            assert reached["stage"] == stage
            if stage == "query_before_result":
                # MVCC read avoids the rights lock held by the paused transaction.
                assert rows(e, "retrieval_queries") == 1 and rows(e, "retrieval_results") == 0
            host.kill()
            assert response.exception(timeout=10) is not None
    finally:
        host.kill()
    if query:
        assert rows(e, "retrieval_queries") == 1
        assert rows(e, "retrieval_results") == (1 if stage == "query_committed" else 0)
    else:
        before = cursor(e)
        expected = {
            "generation_intent": "prepared",
            "projection_written": "building",
            "verification_committed": "verified",
            "publication_committed": "published",
        }[stage]
        assert before["phase"] == expected
        assert rows(e, "index_publications") == (1 if stage == "publication_committed" else 0)
        assert rows(e, "index_verifications") == (
            1 if stage in {"verification_committed", "publication_committed"} else 0
        )
        if stage in {"projection_written", "verification_committed"}:
            expire(e)
    replacement = HttpOwner(python, config, environment, "k" * 32)
    replacement_pid = replacement.process.pid
    try:
        recovered = accepted(replacement, "POST", route, request.model_dump(mode="json"))
        if stage == "verification_committed":
            assert recovered["state"] == "failed"
            assert rows(e, "index_publications") == 0
            fresh = e.request.model_copy(update={"generation_id": "replacement"})
            assert accepted(replacement, "POST", route, fresh.model_dump(mode="json"))["state"] == "published"
        elif query:
            assert [m["score"] for m in recovered["matches"]] == [8.0]
            assert rows(e, "retrieval_results") == 1
        else:
            assert recovered["state"] == "published"
        assert accepted(replacement, "POST", route, request.model_dump(mode="json")) == recovered
        if "status" in reached and stage == "publication_committed":
            assert recovered == reached["status"]
        if "record" in reached:
            assert recovered == reached["record"]
        if stage == "projection_written":
            after = cursor(e)
            assert after["fence"] == before["fence"] + 1 and after["token"] != before["token"]
            with e.engine.connect() as c:
                namespaces = (
                    c.execute(
                        text(
                            "SELECT namespace FROM artifacts.index_build_attempts "
                            "WHERE tenant_id=:tenant AND project_id=:project AND corpus_id='corpus' AND generation_id='g1'"
                        ),
                        e.p.bindings,
                    )
                    .scalars()
                    .all()
                )
            assert len(set(namespaces)) == 2
        assert original_pid != replacement_pid
    finally:
        replacement.close()
    evidence = {
        "timestamp_local": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S"),
        "stage": stage,
        "scope": e.p.scope.model_dump(mode="json"),
        "original_pid": original_pid,
        "replacement_pid": replacement_pid,
        "barrier": reached,
        "recovered": recovered,
        "claim": "Forced process death and installed HTTP replay; no power-loss claim",
    }
    folder = Path(__file__).absolute().parents[5] / ".test-results/retrieval-process-death"
    folder.mkdir(exist_ok=True)
    (folder / (stage + ".json")).write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
