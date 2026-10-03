"""Actual pinned Qdrant oracle with synthetic refs; not Data source admission proof."""

import hashlib
import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from threading import Barrier

import pytest
from amphora_contracts_core import Scope
from amphora_contracts_representations import EncodingProfileRef, RepresentationBindingRef
from amphora_data_artifacts.retrieval.projection import ProjectionPoint, ProjectionSnapshot
from amphora_data_artifacts.retrieval.qdrant.adapter import QdrantAdapter
from amphora_data_artifacts.retrieval.qdrant.collections import path, result
from amphora_data_artifacts.retrieval.qdrant.configuration import IMAGE, QdrantConfiguration
from amphora_data_artifacts.retrieval.qdrant.transport import QdrantError
from amphora_data_artifacts.retrieval.validation import RetrievalError


@pytest.fixture
def backend():
    if os.environ.get("AMPHORA_TEST_QDRANT") != "1":
        pytest.skip("Explicit actual Qdrant fixture opt-in required")
    from qdrant_fixture import owned_state

    state = owned_state()
    assert state["image"] == IMAGE
    return QdrantAdapter(QdrantConfiguration(state["endpoint"], state["api_key"]))


def namespace():
    return "amphora_" + hashlib.sha256(uuid.uuid4().bytes).hexdigest()


def snapshot(count=3):
    scope = Scope(tenant_id="qdrant-oracle", project_id=uuid.uuid4().hex)
    profile = EncodingProfileRef(scope=scope, profile_id="two-dimensional", version="1", sha256="a" * 64)
    points = tuple(
        ProjectionPoint(
            str(uuid.uuid5(uuid.NAMESPACE_URL, scope.project_id + str(i))),
            profile,
            RepresentationBindingRef(
                scope=scope, binding_id="point-" + str(i), sha256=hashlib.sha256(str(i).encode()).hexdigest()
            ),
            ((1.0, 0.0), (0.0, 1.0), (1.0, 1.0))[i % 3],
        )
        for i in range(count)
    )
    return ProjectionSnapshot(2, "dot", points)


@pytest.mark.parametrize("score", [True, float("inf"), float("nan"), 10**400])
def test_score_cannot_import_nonfinite_or_overflowing_authority(score):
    from amphora_data_artifacts.retrieval.qdrant.points import ScoredPoint

    with pytest.raises(RetrievalError, match="score_required"):
        ScoredPoint(snapshot().points[0], score)


def test_actual_build_inspect_repeat_and_independent_dot_oracle(backend):
    name, data = namespace(), snapshot()
    backend.build(name, data)
    backend.build(name, data)
    observed = backend.inspect(name)
    assert observed.dimensions == 2 and observed.metric == "dot"
    assert {p.point_id: p for p in observed.points} == {p.point_id: p for p in data.points}
    scores = backend.query(name, (2.0, 1.0), tuple(p.point_id for p in data.points))
    assert {p.point.binding.binding_id: p.score for p in scores} == {
        "point-0": 2.0,
        "point-1": 1.0,
        "point-2": 3.0,
    }
    filtered = backend.query(name, (2.0, 1.0), (data.points[1].point_id,))
    assert len(filtered) == 1 and filtered[0].score == 1.0
    assert filtered[0].point == data.points[1]
    evidence = {
        "timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "namespace": name, "backend_profile": backend.reference.model_dump(mode="json"),
        "scope": data.points[0].profile.scope.model_dump(mode="json"),
        "point_ids": [p.point_id for p in data.points],
        "query": [2.0, 1.0], "scores": {p.point.binding.binding_id: p.score for p in scores},
        "filtered_point": filtered[0].point.point_id,
        "authority": "Actual Qdrant; synthetic reference fixtures, no Data source admission claim",
    }
    folder = Path(__file__).absolute().parents[5] / ".test-results"
    folder.mkdir(exist_ok=True)
    (folder / "qdrant-adapter-oracle.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


def test_unknown_allowed_point_is_incomplete_not_a_negative_result(backend):
    name, data = namespace(), snapshot()
    backend.build(name, data)
    with pytest.raises(RetrievalError, match="query_incomplete"):
        backend.query(name, (2.0, 1.0), (str(uuid.uuid4()),))
    assert backend.query(name, (2.0, 1.0), ()) == ()


@pytest.mark.parametrize(
    "vectors",
    [
        {"size": 3, "distance": "Dot", "datatype": "float32"},
        {"size": 2, "distance": "Cosine", "datatype": "float32"},
        {"size": 2, "distance": "Dot", "datatype": "float16"},
    ],
)
def test_existing_incompatible_collection_is_never_overwritten(backend, vectors):
    name = namespace()
    assert result(backend.transport.request("PUT", path(name), {"vectors": vectors})) is True
    with pytest.raises(RetrievalError, match="collection_"):
        backend.build(name, snapshot())
    info = backend.collections.read(name)
    assert info["points_count"] == 0
    assert info["config"]["params"]["vectors"]["distance"] == vectors["distance"]


def test_actual_maximum_corpus_batched_writes_and_extra_point_detection(backend):
    name, data = namespace(), snapshot(256)
    backend.build(name, data)
    assert len(backend.inspect(name).points) == 256
    scores = backend.query(name, (2.0, 1.0), tuple(p.point_id for p in data.points))
    assert len(scores) == 256
    extra = {
        "id": str(uuid.uuid4()),
        "vector": [1.0, 1.0],
        "payload": {
            "format": "data.index-point.v1",
            "profile": data.points[0].profile.model_dump(mode="json"),
            "binding": data.points[0].binding.model_dump(mode="json"),
        },
    }
    backend.transport.request("PUT", path(name) + "/points?wait=true", {"points": [extra]})
    with pytest.raises(RetrievalError, match="corpus_bound"):
        backend.inspect(name)


def test_actual_corrupt_payload_is_not_trusted(backend):
    name, data = namespace(), snapshot()
    backend.build(name, data)
    backend.transport.request(
        "PUT",
        path(name) + "/points?wait=true",
        {
            "points": [
                {"id": data.points[0].point_id, "vector": [1.0, 0.0], "payload": {"format": "untrusted"}}
            ]
        },
    )
    with pytest.raises(QdrantError, match="point_shape"):
        backend.inspect(name)


def test_concurrent_creation_uncertainty_recovers_in_fresh_namespace(backend, monkeypatch):
    name, data = namespace(), snapshot()
    other = QdrantAdapter(backend.transport.configuration)
    barrier = Barrier(2, timeout=10)
    for adapter in (backend, other):
        original = adapter.collections.read

        def observed(name, *, missing=False, original=original):
            value = original(name, missing=missing)
            if missing:
                barrier.wait()
            return value

        monkeypatch.setattr(adapter.collections, "read", observed)

    def build(adapter):
        try:
            adapter.build(name, data)
            return "completed"
        except QdrantError as error:
            # Actual1.19.1 can briefly return500 after concurrent create409.
            # No unavailable read is converted into verified content.
            assert str(error) in {"qdrant_http_400", "qdrant_http_409", "qdrant_http_500"}
            return str(error)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(build, (backend, other)))
    assert len(outcomes) == 2
    monkeypatch.undo()
    fresh = namespace()
    backend.build(fresh, data)
    assert {p.point_id: p for p in backend.inspect(fresh).points} == {p.point_id: p for p in data.points}


def test_local_shape_guards_precede_any_backend_effect(backend):
    data = snapshot()
    with pytest.raises(RetrievalError, match="dot_snapshot"):
        backend.build(namespace(), replace(data, metric="cosine"))
    with pytest.raises(RetrievalError, match="duplicate_point"):
        backend.build(namespace(), replace(data, points=(data.points[0], data.points[0])))
    with pytest.raises(RetrievalError, match="mixed_profile"):
        backend.build(
            namespace(),
            replace(
                data,
                points=(
                    data.points[0],
                    replace(
                        data.points[1], profile=data.points[1].profile.model_copy(update={"sha256": "b" * 64})
                    ),
                ),
            ),
        )
    with pytest.raises(RetrievalError, match="duplicate_filter"):
        backend.query(namespace(), (1.0, 2.0), (data.points[0].point_id,) * 2)
    with pytest.raises(RetrievalError, match="namespace"):
        backend.inspect("foreign-collection")
