"""Actual installed HTTP workers racing current rights, fenced leases and heads."""

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

from ...representations.http_support import HttpOwner
from ..test_generation_publication import revoke, rows
from .support import FaultOwner, configuration
from .test_death_replay import cursor, expire

pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(
        os.environ.get("AMPHORA_TEST_QDRANT") != "1", reason="Actual Qdrant required"
    ),
]


def setup(e, tmp_path):
    from qdrant_fixture import owned_state

    state = owned_state()
    config, environment = configuration(e, state, tmp_path)
    python = os.environ.get("AMPHORA_TEST_RETRIEVAL_PROCESS_PYTHON", sys.executable)
    return python, config, environment, state


def evidence(e, name, **details):
    folder = (
        Path(__file__).absolute().parents[5] / ".test-results/retrieval-live-barriers"
    )
    folder.mkdir(exist_ok=True)
    body = {
        "timestamp_local": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S"),
        "scope": e.p.scope.model_dump(mode="json"),
        **details,
    }
    (folder / (name + ".json")).write_text(
        json.dumps(body, indent=2) + "\n", encoding="utf-8"
    )


@pytest.mark.parametrize(
    "stage", ["projection_written", "verification_committed", "query_observed"]
)
def test_revocation_before_commit_blocks_live_worker(generation, tmp_path, stage):
    e = generation
    python, config, environment, state = setup(e, tmp_path)
    query = stage == "query_observed"
    request, route = e.request, "/v1/retrieval/generations"
    if query:
        service = RetrievalService(
            e.ingestion.reads,
            QdrantAdapter(QdrantConfiguration(state["endpoint"], state["api_key"])),
        )
        published = service.advance(e.p, e.request)
        request = RetrieveRepresentations(
            wire_version="1",
            retrieval_id="revoked-live",
            generation=published.generation.reference,
            query=e.binding.reference,
            policy=policy_to_wire(QueryPolicy(1)),
        )
        route = "/v1/retrieval/queries"
    host = FaultOwner(python, config, environment, stage)
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(
                host.call, "POST", route, request.model_dump(mode="json")
            )
            marker = host.events.get(timeout=15)
            assert marker["stage"] == stage
            revoke(e)
            host.release()
            result = future.result(timeout=15)
            assert result.status == 403
        assert rows(e, "retrieval_results") == 0
        assert rows(e, "index_publications") == int(query)
        assert rows(e, "index_verifications") == int(stage != "projection_written")
        evidence(
            e,
            stage,
            pid=host.process.pid,
            barrier=marker,
            status=result.status,
            response=result.json(),
        )
    finally:
        host.kill()


def test_expired_worker_cannot_overwrite_new_attempt(generation, tmp_path):
    e = generation
    python, config, environment, _ = setup(e, tmp_path)
    host = FaultOwner(python, config, environment, "projection_written")
    replacement = HttpOwner(python, config, environment, "k" * 32)
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(
                host.call,
                "POST",
                "/v1/retrieval/generations",
                e.request.model_dump(mode="json"),
            )
            assert host.events.get(timeout=15)["stage"] == "projection_written"
            old = cursor(e)
            expire(e)
            fresh = replacement.call(
                "POST", "/v1/retrieval/generations", e.request.model_dump(mode="json")
            )
            assert fresh.status == 200 and fresh.json()["state"] == "published"
            current = cursor(e)
            assert (
                current["fence"] == old["fence"] + 1
                and current["token"] != old["token"]
            )
            host.release()
            stale = future.result(timeout=15)
            assert (
                stale.status == 409 and "retrieval_stale_claim" in stale.body.decode()
            )
        assert cursor(e) == current
        assert rows(e, "index_build_attempts") == 2
        assert rows(e, "index_verifications") == rows(e, "index_publications") == 1
        evidence(
            e,
            "stale_lease",
            old_pid=host.process.pid,
            new_pid=replacement.process.pid,
            stale_status=stale.status,
            published=fresh.json(),
        )
    finally:
        host.kill()
        replacement.close()


def test_two_processes_compete_for_one_head(generation, tmp_path):
    e = generation
    python, config, environment, _ = setup(e, tmp_path)
    left = FaultOwner(python, config, environment, "verification_committed")
    right = FaultOwner(python, config, environment, "verification_committed")
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            requests = [e.request, e.request.model_copy(update={"generation_id": "g2"})]
            futures = [
                pool.submit(
                    host.call,
                    "POST",
                    "/v1/retrieval/generations",
                    request.model_dump(mode="json"),
                )
                for host, request in zip((left, right), requests, strict=True)
            ]
            markers = [host.events.get(timeout=15) for host in (left, right)]
            assert all(m["stage"] == "verification_committed" for m in markers)
            assert (
                rows(e, "index_verifications") == 2
                and rows(e, "index_publications") == 0
            )
            left.release()
            right.release()
            results = [future.result(timeout=15) for future in futures]
            assert sorted(r.status for r in results) == [200, 409]
            assert (
                "retrieval_head_conflict"
                in next(r for r in results if r.status == 409).body.decode()
            )
        assert rows(e, "index_publications") == rows(e, "index_heads") == 1
        evidence(
            e,
            "competing_publishers",
            pids=[left.process.pid, right.process.pid],
            barriers=markers,
            results=[{"status": r.status, "body": r.json()} for r in results],
        )
    finally:
        left.kill()
        right.kill()
