import copy
import json
from pathlib import Path

import pytest
from amphora_agent_planning.metadata_reads import MetadataTransport, MetadataWindow
from amphora_agent_planning.metadata_reads.targets import target
from amphora_agent_planning.retrieval_access import (
    RetrievalObservation,
    RetrievalReader,
    RetrievalSelection,
)
from amphora_agent_planning.retrieval_access.identity import fingerprint
from amphora_contracts_representations import RetrievalRecord, RetrieveRepresentations

from ..campaign_context.test_selection import request
from ..metadata_reads.test_transport import server  # noqa: F401
from ..registry_access.test_discovery import Scripted


def values():
    return json.loads((Path(__file__).parent / "fixtures/retrieval.json").read_bytes())


def query(raw=None):
    return RetrieveRepresentations.model_validate_json(json.dumps(values()["query"] if raw is None else raw))


def record(raw=None):
    return RetrievalRecord.model_validate_json(json.dumps(values()["record"] if raw is None else raw))


def selected(value=None, digest=None):
    return RetrievalSelection.bind(request(), query() if value is None else value, record().sha256 if digest is None else digest)


def test_literal_installed_data_vector_preserves_provenance_and_negative_ties():
    observation = RetrievalObservation.bind(selected(), record())
    assert observation.document() == record()
    assert observation.document().query_sha256 == "0e8ca17606c12b7258850732d2df75a3f16ed3caf97de1ff28bf3f70caa2ce23"
    assert observation.document().sha256 == "d6c5c259b6a0bf9abd201d1aa63b16e121fb3095b35bac0e72c594a3d87c8ea6"
    assert all(match.score == -2.0 for match in observation.document().matches)
    assert len(selected().sha256) == 64


@pytest.mark.parametrize("fault,code", [("actor", "identity"), ("generation", "identity"), ("query", "identity"),
    ("query-digest", "query_digest"), ("result-digest", "result_digest"), ("provenance", "binding_digest"),
    ("scope", "scope"), ("span", "span"), ("duplicate", "duplicate_binding"), ("order", "order")])
def test_misbound_and_altered_results_are_rejected(fault, code):
    raw = values()["record"]
    if fault == "actor":
        raw["actor_id"] = "another"
    elif fault == "generation":
        raw["generation"]["generation_id"] = "new"
    elif fault == "query":
        raw["query"]["reference"]["binding_id"] = "new"
    elif fault == "query-digest":
        raw["query_sha256"] = "f" * 64
    elif fault == "result-digest":
        raw["sha256"] = "f" * 64
    elif fault == "provenance":
        raw["matches"][0]["binding"]["source"]["source"]["revision_id"] = "r2"
    elif fault == "scope":
        raw["matches"][0]["binding"]["vector"]["scope"]["project_id"] = "other"
    elif fault == "span":
        raw["matches"][0]["binding"]["source"]["end"] = 100
    elif fault == "duplicate":
        raw["matches"][1] = copy.deepcopy(raw["matches"][0])
    else:
        raw["matches"].reverse()
    with pytest.raises(ValueError, match="retrieval_context_" + code):
        RetrievalObservation.bind(selected(), record(raw))


def test_expected_result_pin_is_required_and_not_replaced_by_peer():
    with pytest.raises(ValueError, match="retrieval_context_result_digest"):
        RetrievalObservation.bind(selected(digest="f" * 64), record())
    for digest in (None, "bad", True):
        with pytest.raises(ValueError, match="retrieval_context_result_pin"):
            RetrievalSelection.bind(request(), query(), digest)


def test_filter_order_is_canonical_but_empty_and_all_are_distinct():
    raw = values()["query"]
    refs = [match["binding"]["reference"] for match in values()["record"]["matches"]]
    raw["policy"]["bindings"] = refs
    first = selected(query(raw))
    raw["policy"]["bindings"] = list(reversed(refs))
    assert selected(query(raw)) == first
    raw["policy"]["bindings"] = []
    assert selected(query(raw)).sha256 != selected().sha256
    raw["policy"]["bindings"] = refs * 2
    with pytest.raises(ValueError, match="retrieval_context_duplicate_binding"):
        selected(query(raw))


@pytest.mark.parametrize("fault", ["scope", "query-scope", "filter-scope", "boolean-k"])
def test_foreign_or_forged_request_rejects_before_io(fault):
    raw = values()["query"]
    if fault == "scope":
        raw["generation"]["scope"]["project_id"] = "other"
    elif fault == "query-scope":
        raw["query"]["scope"]["project_id"] = "other"
    elif fault == "filter-scope":
        ref = values()["record"]["matches"][0]["binding"]["reference"]
        ref["scope"]["project_id"] = "other"
        raw["policy"]["bindings"] = [ref]
    else:
        value = query().model_copy(update={"policy": query().policy.model_copy(update={"top_k": True})})
        with pytest.raises(ValueError):
            selected(value)
        return
    with pytest.raises(ValueError, match="retrieval_context_scope"):
        selected(query(raw))


def rehash_query(raw):
    raw["query_sha256"] = fingerprint({"format": "data.retrieval-query.v1", "retrieval_id": raw["retrieval_id"],
        "actor_id": raw["actor_id"], "generation": raw["generation"], "query": raw["query"], "policy": raw["policy"]})


def test_top_k_and_explicit_allow_set_are_not_similarity_suggestions():
    raw = values()["record"]
    raw["policy"]["top_k"] = 1
    rehash_query(raw)
    chosen = query().model_copy(update={"policy": record(raw).policy})
    with pytest.raises(ValueError, match="retrieval_context_top_k"):
        RetrievalObservation.bind(selected(chosen), record(raw))
    raw = values()["record"]
    raw["policy"]["bindings"] = []
    rehash_query(raw)
    chosen = query().model_copy(update={"policy": record(raw).policy})
    with pytest.raises(ValueError, match="retrieval_context_filter"):
        RetrievalObservation.bind(selected(chosen), record(raw))


def test_same_dimensions_do_not_substitute_for_exact_profile():
    raw = values()["record"]
    value = raw["matches"][0]["binding"]
    value["profile"]["sha256"] = "f" * 64
    value["reference"]["sha256"] = fingerprint({"format": "data.representation-binding.v1",
        "binding_id": value["reference"]["binding_id"], "scope": value["reference"]["scope"],
        "profile": value["profile"], "source": value["source"], "vector": value["vector"]}, 65536)
    with pytest.raises(ValueError, match="retrieval_context_profile"):
        RetrievalObservation.bind(selected(), record(raw))


def test_exact_get_authenticated_and_data_only_routes(server):  # noqa: F811
    host, _ = server
    host.body = record().model_dump_json().encode()
    transport = MetadataTransport("data", f"http://127.0.0.1:{host.server_port}", "t" * 32)
    result = RetrievalReader(transport).read(selected())
    assert result.failure is None and result.record.document() == record() and result.calls == 1
    assert host.calls == [("/v1/retrieval/queries/retrieval-1", "Bearer " + "t" * 32)]
    for owner, path in (("data", "/v1/releases?limit=1"), ("registry", "/v1/retrieval/queries/retrieval-1"),
                        ("data", "/v1/retrieval/queries/retrieval-1?new=true"), ("data", "/v1/retrieval/queries")):
        with pytest.raises(ValueError):
            target(owner, path)
    assert MetadataWindow("data").max_calls == 32


@pytest.mark.parametrize("status,code", [(403, "metadata_denied"), (404, "metadata_missing"), (409, "metadata_unavailable")])
def test_denied_missing_pending_do_not_rerun_or_expose_result(server, status, code):  # noqa: F811
    host, _ = server
    host.status, host.body = status, b"SECRET"
    result = RetrievalReader(MetadataTransport("data", f"http://127.0.0.1:{host.server_port}", "t" * 32)).read(selected())
    assert result.record is None and result.failure == code and len(host.calls) == 1


def test_invalid_peer_record_and_programming_error_remain_distinct():
    bad = record().model_copy(update={"sha256": "f" * 64})
    result = RetrievalReader(Scripted(bad)).read(selected())
    assert result.record is None and result.failure == "retrieval_context_invalid"
    with pytest.raises(ValueError, match="bug"):
        RetrievalReader(Scripted(ValueError("bug"))).read(selected())
    with pytest.raises(ValueError, match="metadata_window"):
        RetrievalReader(None).read(selected(), MetadataWindow("registry"))


def test_boolean_score_cannot_normalize_into_a_numeric_observation():
    original = record()
    bad = original.model_copy(update={"matches": (original.matches[0].model_copy(update={"score": True}),
                                                 original.matches[1])})
    result = RetrievalReader(Scripted(bad)).read(selected())
    assert result.record is None and result.failure == "retrieval_context_invalid"
