"""Pinned scientific intent keeps weak outcomes and exact authenticated dependencies."""
from dataclasses import replace

import pytest
from amphora_research.scientific_api.boundary import ScientificInputError
from amphora_research.scientific_api.intent import ScientificIntent
from amphora_research.scientific_api.resolution import ScientificInputResolver

from .test_resolution import resolution_case


@pytest.mark.parametrize("kind",["eligibility","synthesis"])
def test_roundtrip_and_weak_result_status(kind):
    bound,reader = resolution_case(kind)
    intent = ScientificIntent.prepare(bound)
    assert ScientificIntent.restore(intent.content) == intent
    assert intent.status().outcome.status == "pending"
    decision = intent.document(ScientificInputResolver(reader).resolve(bound)).record
    assert intent.status(decision).outcome.decision == decision
    with pytest.raises(ScientificInputError,match="decision_mismatch"):
        intent.status(decision.model_copy(update={"actor_id":"other"}))


@pytest.mark.parametrize("fault,reason",[("bound","resolution_mismatch"),("empty","input_limit"),
    ("duplicate","input_duplicate"),("report","report_missing"),("dependency","dependency_missing")])
def test_cannot_drop_or_substitute_consumed_dependencies(fault,reason):
    bound,reader = resolution_case()
    resolved = ScientificInputResolver(reader).resolve(bound)
    if fault == "bound":
        resolved = replace(resolved,bound=replace(bound,actor="other"))
    elif fault == "empty":
        resolved = replace(resolved,inputs=())
    elif fault == "duplicate":
        resolved = replace(resolved,inputs=resolved.inputs+resolved.inputs[:1])
    elif fault == "report":
        resolved = replace(resolved,inputs=tuple(x for x in resolved.inputs if x not in bound.request.reports))
    else:
        resolved = replace(resolved,inputs=bound.request.reports)
    with pytest.raises(ScientificInputError,match=reason):
        ScientificIntent.prepare(bound).document(resolved)
