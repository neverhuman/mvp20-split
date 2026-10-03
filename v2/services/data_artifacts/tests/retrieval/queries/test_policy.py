"""Independent ranking oracles and hostile identity/shape cases; no storage claim."""

import itertools
import math
from dataclasses import replace

import pytest
from amphora_contracts_representations import RetrieveRepresentations
from amphora_data_artifacts.representations.fixture import FixtureEncoder, fixture_profile
from amphora_data_artifacts.representations.validation import RepresentationError
from amphora_data_artifacts.retrieval.identity import GenerationPlan
from amphora_data_artifacts.retrieval.manifest import CorpusManifest
from amphora_data_artifacts.retrieval.mapping import reference_to_wire
from amphora_data_artifacts.retrieval.queries.identity import QueryPlan
from amphora_data_artifacts.retrieval.queries.mapping import (
    plan_from_request,
    policy_from_wire,
    policy_to_wire,
    record_from_wire,
    record_to_wire,
)
from amphora_data_artifacts.retrieval.queries.policy import BindingScore, QueryPolicy
from amphora_data_artifacts.retrieval.queries.records import QueryRecord
from amphora_data_artifacts.retrieval.validation import RetrievalError

from ..test_generation_models import BACKEND, PROFILE, SCOPE, binding


@pytest.fixture
def plan():
    manifest = CorpusManifest(SCOPE, PROFILE, tuple(binding(i) for i in range(3)))
    generation = GenerationPlan("corpus", "g1", "publisher", manifest, None, BACKEND)
    return QueryPlan("query1", "reader", generation, binding(9), QueryPolicy(2))


def test_ranking_is_independent_of_backend_order_and_keeps_negative_scores(plan):
    members = plan.generation.manifest.bindings
    scores = tuple(BindingScore(b.reference, -2) for b in members)
    expected = tuple(sorted(scores, key=lambda s: (s.binding.binding_id, s.binding.sha256)))[:2]
    for permutation in itertools.permutations(scores):
        assert plan.policy.rank(members, permutation) == expected
    distinct = tuple(BindingScore(b.reference, score) for b, score in zip(members, (-8, 0, 3), strict=True))
    assert plan.policy.rank(members, distinct) == (distinct[2], distinct[1])
    assert QueryPolicy(256).rank((), ()) == ()


def test_filter_is_set_canonical_with_explicit_empty_distinct_from_all(plan):
    manifest = plan.generation.manifest
    refs = tuple(b.reference for b in manifest.bindings)
    first = QueryPolicy(2, refs)
    second = QueryPolicy(2, tuple(reversed(refs)))
    assert first == second
    assert replace(plan, policy=first).sha256 == replace(plan, policy=second).sha256
    assert QueryPolicy(2, ()).select(manifest) == ()
    assert QueryPolicy(2).select(manifest) == manifest.bindings
    assert replace(plan, policy=QueryPolicy(2, ())).sha256 != plan.sha256
    for ref, code in (
        (refs[0].model_copy(update={"sha256": "0" * 64}), "filter_member"),
        (binding(7).reference, "filter_member"),
        (refs[0].model_copy(update={"scope": SCOPE.model_copy(update={"project_id": "other"})}), "filter_scope"),
    ):
        with pytest.raises(RetrievalError, match=code):
            replace(plan, policy=QueryPolicy(1, (ref,)))


@pytest.mark.parametrize("value", [True, False, 0, -1, 257, 1.0, "1"])
def test_top_k_bound_is_strict(value):
    with pytest.raises(RetrievalError, match="top_k"):
        QueryPolicy(value)


@pytest.mark.parametrize("value", [True, False, float("nan"), float("inf"), -float("inf"), 10**400, "2"])
def test_nonfinite_or_non_numeric_scores_fail(value):
    with pytest.raises(RetrievalError, match="score_finite"):
        BindingScore(binding(1).reference, value)


def test_signed_zero_and_integer_score_are_canonical():
    ref = binding(1).reference
    assert math.copysign(1, BindingScore(ref, -0.0).value) == 1
    assert BindingScore(ref, 2) == BindingScore(ref, 2.0)


def test_score_set_cannot_hide_missing_duplicate_or_foreign_results(plan):
    members = plan.generation.manifest.bindings
    scores = tuple(BindingScore(b.reference, 2) for b in members)
    for eligible, observed, code in (
        (members, scores[:-1], "scores_incomplete"),
        (members, scores + (scores[0],), "score_duplicate"),
        (members, (BindingScore(binding(8).reference, 2),), "score_member"),
        (members, (None,), "score_required"),
        (members + (members[0],), scores, "eligible_duplicate"),
        (list(members), scores, "eligible_bound"),
        (members, list(scores), "scores_bound"),
    ):
        with pytest.raises(RetrievalError, match=code):
            plan.policy.rank(eligible, observed)


def test_query_identity_captures_actor_generation_binding_profile_and_policy(plan, monkeypatch):
    variants = (
        replace(plan, actor_id="other"), replace(plan, retrieval_id="other"),
        replace(plan, generation=replace(plan.generation, generation_id="g2")),
        replace(plan, query=binding(8)), replace(plan, policy=QueryPolicy(1)),
    )
    assert len({plan.sha256, *(p.sha256 for p in variants)}) == 6
    with pytest.raises(RetrievalError, match="query_profile"):
        replace(plan, query=binding(9, profile=fixture_profile("l2")))
    with pytest.raises(RepresentationError, match="binding_scope"):
        replace(plan, query=binding(9, scope=SCOPE.model_copy(update={"project_id": "other"})))
    profile = replace(PROFILE, space=replace(PROFILE.space, metric="euclidean"))
    # Synthetic descriptor only: this does not claim an installed Euclidean encoder.
    monkeypatch.setattr(FixtureEncoder, "available", lambda self, candidate: True)
    manifest = CorpusManifest(SCOPE, profile, (binding(0, profile=profile),))
    with pytest.raises(RetrievalError, match="query_metric"):
        replace(plan, generation=replace(plan.generation, manifest=manifest), query=binding(9, profile=profile))


def test_wire_request_resolves_exact_owner_records_and_rejects_forgery(plan):
    request = RetrieveRepresentations(
        wire_version="1", retrieval_id=plan.retrieval_id,
        generation=reference_to_wire(plan.generation.reference), query=plan.query.reference,
        policy=policy_to_wire(plan.policy),
    )
    assert plan_from_request(plan.actor_id, request, plan.generation, plan.query) == plan
    for change, code in (
        ({"generation": request.generation.model_copy(update={"sha256": "0" * 64})}, "query_generation"),
        ({"query": binding(8).reference}, "query_binding"),
    ):
        with pytest.raises(RetrievalError, match=code):
            plan_from_request(plan.actor_id, request.model_copy(update=change), plan.generation, plan.query)
    with pytest.raises(RepresentationError, match="wire_shape"):
        policy_from_wire(request.policy.model_copy(update={"top_k": True}))


def test_result_roundtrip_preserves_full_provenance_and_rejects_tampering(plan):
    members = plan.generation.manifest.bindings
    scores = tuple(BindingScore(b.reference, 3 - i) for i, b in enumerate(members))
    result = QueryRecord(plan, plan.policy.rank(members, scores))
    wire = record_to_wire(result)
    assert record_from_wire(plan.generation, wire) == result
    assert wire.matches[0].binding == members[0]
    empty = QueryRecord(replace(plan, policy=QueryPolicy(2, ())), ())
    assert record_from_wire(plan.generation, record_to_wire(empty)) == empty
    changes = (
        ({"actor_id": "other"}, "query_digest"),
        ({"sha256": "0" * 64}, "result_digest"),
        ({"generation": wire.generation.model_copy(update={"sha256": "0" * 64})}, "query_generation"),
        ({"matches": (wire.matches[0].model_copy(update={"binding": members[0].model_copy(update={"vector": members[1].vector})}), wire.matches[1])}, "result_projection"),
    )
    for change, code in changes:
        with pytest.raises(RetrievalError, match=code):
            record_from_wire(plan.generation, wire.model_copy(update=change))
    with pytest.raises(RetrievalError, match="matches_order"):
        QueryRecord(plan, tuple(reversed(result.matches)))
    with pytest.raises(RetrievalError, match="matches_bound"):
        QueryRecord(plan, scores)
    with pytest.raises(RetrievalError, match="match_member"):
        QueryRecord(plan, (BindingScore(binding(8).reference, 3),))


def test_filter_bounds_and_domain_type_guards(plan):
    ref = plan.query.reference
    for value, code in (([ref], "filter_bound"), ((ref,) * 257, "filter_bound"), ((ref, ref), "filter_duplicate")):
        with pytest.raises(RetrievalError, match=code):
            QueryPolicy(1, value)
    for change, code in (({"generation": None}, "plan_required"), ({"policy": None}, "policy_required")):
        with pytest.raises(RetrievalError, match=code):
            replace(plan, **change)
    with pytest.raises(RetrievalError, match="query_required"):
        QueryRecord(None, ())
    with pytest.raises(RetrievalError, match="score_required"):
        QueryRecord(plan, (None,))
    with pytest.raises(RetrievalError, match="policy_required"):
        policy_to_wire(None)
    with pytest.raises(RetrievalError, match="record_required"):
        record_to_wire(None)
