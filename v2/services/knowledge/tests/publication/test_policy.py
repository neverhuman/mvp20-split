import pytest
from amphora_contracts_knowledge import IncompleteReasoning
from amphora_knowledge.authoring.canonical import KnowledgeError
from amphora_knowledge.publication.policy import LogicalReceiptPolicy


@pytest.mark.parametrize("positive,negative,complete,status,expected", [
    (True, False, True, "supported", ("accepted", None)),
    (False, True, True, "contradicted", ("rejected", "logical_contradicted")),
    (False, False, True, "unknown", ("abstained", "logical_unknown")),
    (True, True, True, "unknown", ("abstained", "logical_conflict")),
    (True, False, False, "unknown", ("abstained", "logical_incomplete")),
    (False, True, False, "unknown", ("abstained", "logical_incomplete")),
])
def test_dispositions_keep_missing_conflicting_and_incomplete_distinct(payload_case, positive, negative, complete, status, expected):
    result = payload_case[2].decision.result
    finding = result.findings[0].model_copy(update={"positive": positive, "negative": negative,
        "conflict": positive and negative, "status": status})
    result = result.model_copy(update={"findings": (finding,)})
    if not complete:
        result = result.model_copy(update={"outcome": IncompleteReasoning(status="incomplete", code="reasoning_work_limit")})
    assert LogicalReceiptPolicy.disposition(result) == expected


@pytest.mark.parametrize("change", ["missing", "foreign", "false_support", "hidden_conflict"])
def test_findings_cannot_omit_targets_or_invent_support(payload_case, change):
    result = payload_case[2].decision.result
    finding = result.findings[0]
    if change == "missing":
        findings = ()
    elif change == "foreign":
        findings = (finding.model_copy(update={"target": finding.target.model_copy(update={"predicate": "other"})}),)
    elif change == "false_support":
        findings = (finding.model_copy(update={"positive": False}),)
    else:
        findings = (finding.model_copy(update={"negative": True, "status": "unknown", "conflict": False}),)
    with pytest.raises(KnowledgeError, match="publication_findings_mismatch"):
        LogicalReceiptPolicy.disposition(result.model_copy(update={"findings": findings}))


def test_all_requested_targets_are_required_for_acceptance(payload_case):
    result = payload_case[2].decision.result
    first = result.findings[0]
    target = first.target.model_copy(update={"predicate": "another"})
    unknown = first.model_copy(update={"target": target, "positive": False, "status": "unknown"})
    result = result.model_copy(update={"request": result.request.model_copy(update={"targets": (*result.request.targets, target)}),
                                      "findings": (*result.findings, unknown)})
    assert LogicalReceiptPolicy.disposition(result) == ("abstained", "logical_unknown")
