"""Independently specified scenario invariants; no actual scientific owner claim."""

import copy
import hashlib
import json

import pytest

from .protocol.manifest import MAX_BYTES, ManifestError, ScenarioManifest


@pytest.fixture
def document():
    scope = {"tenant_id": "fixture", "project_id": "feedback"}
    schema = {"schema_id": "fixture.record", "version": "1", "sha256": "a" * 64}

    def ref(field, value):
        return {"scope": scope.copy(), field: value, "revision": 1}

    def artifact(name):
        return {
            "artifact_id": name,
            "scope": scope.copy(),
            "sha256": "b" * 64,
            "media_type": "text/plain",
            "schema_ref": schema.copy(),
            "size_bytes": 4,
        }

    graph = {"scope": scope.copy(), "graph_id": "domain"}
    return {
        "format": "amphora.knowledge-feedback-fixture.v1",
        "authority": "declared_fixture_only",
        "scenario_id": "iteration-one",
        "scope": scope,
        "question": {
            "question": ref("question_id", "question"),
            "need": ref("need_id", "need"),
            "method": schema.copy(),
        },
        "source": {
            "span": {
                "source": {
                    "scope": scope.copy(),
                    "source_id": "source",
                    "revision_id": "r1",
                    "raw": artifact("source-bytes"),
                },
                "unit": "byte",
                "start": 0,
                "end": 4,
                "sha256": hashlib.sha256(b"ABBA").hexdigest(),
            },
            "trace": {"scope": scope.copy(), "trace_id": "trace", "sha256": "c" * 64},
        },
        "graph": {
            "snapshot": {"graph": graph, "revision": 1, "sha256": "d" * 64},
            "assertion": {
                "graph": copy.deepcopy(graph),
                "assertion_id": "claim",
                "revision": 1,
            },
        },
        "specimens": [
            {
                "key": "prepared-a",
                "candidate": ref("candidate_id", "candidate"),
                "material": ref("material_state_id", "state-a"),
                "sample": ref("sample_id", "sample-a"),
                "experiment": ref("experiment_id", "experiment"),
                "observation": ref("observation_id", "observation-a"),
            }
        ],
        "representation": {
            "profile": {
                "scope": scope.copy(),
                "profile_id": "profile",
                "version": "1",
                "sha256": "e" * 64,
            },
            "generation": {
                "scope": scope.copy(),
                "corpus_id": "corpus",
                "generation_id": "g1",
                "sha256": "f" * 64,
            },
        },
        "campaign": {
            "cut": {
                "scope": scope.copy(),
                "run_id": "campaign",
                "plan_sha256": "1" * 64,
                "revision": 1,
                "frontier_revision": 1,
            },
            "receipt": artifact("receipt"),
        },
        "views": [
            {
                "owner": "knowledge",
                "view_id": "neighborhood",
                "version": "1",
                "result_schema": schema.copy(),
            }
        ],
    }


def parse(document):
    return ScenarioManifest.parse(json.dumps(document).encode())


def test_canonical_pin_snapshot_is_detached_and_has_no_acceptance_authority(document):
    manifest = parse(document)
    expected = json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    assert manifest.canonical_bytes == expected
    assert manifest.sha256 == hashlib.sha256(expected).hexdigest()
    assert ScenarioManifest.parse(expected) == manifest
    assert parse(dict(reversed(list(document.items())))) == manifest
    document["scenario_id"] = "changed"
    assert manifest.document().scenario_id == "iteration-one"
    assert manifest.document().authority == "declared_fixture_only"
    altered = manifest.document().model_copy(
        update={"authority": "scientifically_accepted"}
    )
    with pytest.raises(ValueError):
        ScenarioManifest(altered)
    with pytest.raises(ManifestError, match="document"):
        ScenarioManifest(document)


@pytest.mark.parametrize(
    "path",
    [
        ("question", "question", "scope"),
        ("source", "span", "source", "raw", "scope"),
        ("source", "trace", "scope"),
        ("graph", "assertion", "graph", "scope"),
        ("representation", "generation", "scope"),
        ("campaign", "receipt", "scope"),
        ("specimens", 0, "sample", "scope"),
    ],
)
def test_foreign_nested_scope_cannot_be_hidden_in_manifest(document, path):
    value = document
    for key in path:
        value = value[key]
    value["project_id"] = "foreign"
    with pytest.raises(ManifestError, match="scope"):
        parse(document)


@pytest.mark.parametrize(
    "start,end,size,code",
    [
        (2, 2, 4, "span"),
        (3, 2, 4, "span"),
        (0, 5, 4, "span"),
        (0, 65537, 65537, "window"),
    ],
)
def test_source_span_is_bounded_but_bytes_remain_owner_verified(
    document, start, end, size, code
):
    span = document["source"]["span"]
    span.update(start=start, end=end)
    span["source"]["raw"]["size_bytes"] = size
    with pytest.raises(ManifestError, match=code):
        parse(document)


def test_same_candidate_keeps_distinct_preparations_and_observations(document):
    other = copy.deepcopy(document["specimens"][0])
    other.update(key="prepared-b")
    other["material"]["material_state_id"] = "state-b"
    other["sample"]["sample_id"] = "sample-b"
    other["observation"]["observation_id"] = "observation-b"
    document["specimens"].append(other)
    manifest = parse(document)
    specimens = manifest.document().specimens
    assert len(specimens) == 2 and specimens[0].candidate == specimens[1].candidate
    assert specimens[0].material != specimens[1].material
    document["specimens"].reverse()
    assert parse(document).sha256 != manifest.sha256


@pytest.mark.parametrize("kind", ["specimen", "sample", "observation", "view", "graph"])
def test_ambiguous_or_mismatched_pins_are_rejected(document, kind):
    if kind == "graph":
        document["graph"]["assertion"]["graph"]["graph_id"] = "other"
    elif kind == "view":
        document["views"].append(copy.deepcopy(document["views"][0]))
    else:
        other = copy.deepcopy(document["specimens"][0])
        if kind != "specimen":
            other["key"] = "other"
        if kind == "observation":
            other["sample"]["sample_id"] = "other"
        document["specimens"].append(other)
    with pytest.raises(ManifestError, match=kind):
        parse(document)


@pytest.mark.parametrize(
    "path",
    [
        ("graph", "snapshot", "sha256"),
        ("representation", "profile", "sha256"),
        ("campaign", "receipt", "sha256"),
        ("source", "trace", "sha256"),
    ],
)
def test_successor_pin_changes_fingerprint_without_rewriting_predecessor(
    document, path
):
    original = parse(document)
    value = document
    for key in path[:-1]:
        value = value[key]
    value[path[-1]] = "2" * 64
    successor = parse(document)
    assert successor.sha256 != original.sha256
    assert ScenarioManifest.parse(original.canonical_bytes) == original


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b" " * (MAX_BYTES + 1),
        b'{"x":1,"x":2}',
        b'{"x":NaN}',
        b"\xff",
        b"[" * 10000 + b"]" * 10000,
        b'{"x":1e999}',
    ],
    ids=["empty", "oversized", "duplicate", "nan", "invalid-utf8", "deep-json", "overflow"],
)
def test_unsafe_or_ambiguous_json_fails_before_any_owner_work(raw):
    with pytest.raises(ValueError):
        ScenarioManifest.parse(raw)


def test_credential_fields_and_unbounded_collections_are_not_part_of_protocol(document):
    document["token"] = "not-a-credential-field"
    with pytest.raises(ValueError):
        parse(document)
    del document["token"]
    document["views"] *= 17
    with pytest.raises(ValueError):
        parse(document)
