import copy
import json
from pathlib import Path

import pytest
from amphora_agent_planning.campaign_context import ResearchSelection
from amphora_agent_planning.context import RequestSnapshot
from amphora_contracts_core import Scope
from amphora_contracts_planning import CampaignResearchSelection

FIXTURES = Path(__file__).parent / "fixtures"
SCOPE = Scope(tenant_id="planning-fixture", project_id="context")


def request(value=None):
    raw = (FIXTURES / "request.json").read_bytes() if value is None else json.dumps(value).encode()
    return RequestSnapshot.from_bytes(raw, actor_id="fixture", scope=SCOPE)


def document():
    return json.loads((FIXTURES / "selection.json").read_bytes())


def bind(value=None, original=None):
    return ResearchSelection.from_bytes(json.dumps(document() if value is None else value).encode(),
                                        request() if original is None else original)


def test_literal_identity_and_caller_mutation_cannot_change_selection():
    value = document()
    selected = bind(value)
    expected = json.loads((FIXTURES / "identity.json").read_bytes())
    assert selected.sha256 == expected["canonical_sha256"]
    assert selected.request.sha256 == expected["request_sha256"]
    assert bind(dict(reversed(list(value.items())))) == selected
    value["questions"].clear()
    assert len(selected.document().questions) == 1
    forged = selected.document().model_copy(update={"questions": ()})
    with pytest.raises(ValueError, match="campaign_context_question_unselected"):
        ResearchSelection.bind(forged, selected.request)
    assert ResearchSelection.bind(selected.document(), selected.request) == selected


@pytest.mark.parametrize("path,value,code", [
    (("engagement", "engagement_id"), "other", "campaign_context_engagement"),
    (("engagement", "scope", "project_id"), "foreign", "campaign_context_engagement"),
    (("request_sha256",), "f" * 64, "campaign_context_request"),
    (("questions", 0, "scope", "project_id"), "foreign", "campaign_context_scope"),
    (("needs", 0, "scope", "project_id"), "foreign", "campaign_context_scope"),
    (("assessments", 0, "request", "profile", "scope", "project_id"), "foreign", "campaign_context_scope"),
    (("assessments", 0, "request", "question", "scope", "project_id"), "foreign", "campaign_context_scope"),
    (("assessments", 0, "request", "question", "revision"), 2, "campaign_context_question_unselected"),
    (("assessments", 0, "request", "answers", 0, "artifact", "scope", "project_id"), "foreign", "campaign_context_scope"),
    (("assessments", 0, "request", "receipts", 0, "scope", "project_id"), "foreign", "campaign_context_scope"),
    (("assessments", 0, "request", "answers", 0, "artifact", "sha256"), "f" * 64, "campaign_context_artifact_unselected"),
    (("assessments", 0, "request", "receipts", 0, "artifact_id"), "invented", "campaign_context_artifact_unselected"),
], ids=["engagement", "engagement_scope", "request", "question_scope", "need_scope", "profile_scope",
        "assessment_question_scope", "question_revision", "answer_scope", "receipt_scope", "answer_hash", "receipt_identity"])
def test_scope_and_exact_selection_guards(path, value, code):
    source = document()
    item = source
    for key in path[:-1]:
        item = item[key]
    item[path[-1]] = value
    with pytest.raises(ValueError, match=code):
        bind(source)


@pytest.mark.parametrize("variant,code", [
    ("questions", "duplicate_reference"), ("needs", "duplicate_reference"),
    ("assessments", "duplicate_assessment"), ("answers", "duplicate_criterion"),
    ("receipts", "duplicate_receipt"),
])
def test_duplicate_identities_are_not_a_larger_context(variant, code):
    source = document()
    values = source[variant] if variant in {"questions", "needs", "assessments"} else source["assessments"][0]["request"][variant]
    values.append(copy.deepcopy(values[0]))
    with pytest.raises(ValueError, match="campaign_context_" + code):
        bind(source)


def test_explicit_historical_revisions_remain_distinct_without_latest_selection():
    source = document()
    source["questions"].append({**source["questions"][0], "revision": 2})
    selected = bind(source)
    assert [ref.revision for ref in selected.document().questions] == [1, 2]
    assert selected.document().assessments[0].request.question.revision == 1
    source["questions"].reverse()
    assert bind(source).sha256 != selected.sha256  # Authored selection ordering is retained.


def test_empty_selection_is_not_invented_scientific_context():
    source = document()
    for field in ("questions", "needs", "assessments"):
        source[field] = []
    assert bind(source).document().assessments == ()


def test_request_purpose_and_actual_original_bytes_are_revalidated():
    source = json.loads((FIXTURES / "request.json").read_bytes())
    source["purpose"] = "knowledge_decomposition"
    original = request(source)
    selection = document()
    selection["request_sha256"] = original.sha256
    with pytest.raises(ValueError, match="campaign_context_purpose"):
        bind(selection, original)
    source["purpose"] = "supervision"
    source["runtime_cut"] = {"scope": SCOPE.model_dump(), "run_id": "run", "plan_sha256": "c" * 64,
                             "revision": 1, "frontier_revision": 1}
    original = request(source)
    selection["request_sha256"] = original.sha256
    assert bind(selection, original).request == original
    malformed = json.loads(original.canonical)
    malformed["context"]["limits"]["total_tokens"] = 1
    with pytest.raises(ValueError, match="insufficient_attempt_budget"):
        bind(selection, RequestSnapshot(json.dumps(malformed).encode()))


def test_omitted_evidence_is_not_authorized_by_an_assessment_reference():
    source = document()
    source["assessments"][0]["request"]["receipts"] = [request().document().context.omissions[0].artifact.model_dump(mode="json")]
    with pytest.raises(ValueError, match="campaign_context_artifact_unselected"):
        bind(source)


@pytest.mark.parametrize("raw,code", [
    (b"", "campaign_context_size"), (b"x" * 262145, "campaign_context_size"),
    ("{}", "campaign_context_size"), (b"\xff", "invalid_campaign_context_selection"),
    (b"{", "invalid_campaign_context_selection"), (b"[]", "invalid_campaign_context_selection"),
    (b'{"x":1,"x":2}', "duplicate_json_key"), (b'{"x":NaN}', "nonfinite_json"),
    (b"[" * 1100, "invalid_campaign_context_selection"),
], ids=["empty", "large", "not_bytes", "utf8", "syntax", "array", "duplicate_key", "nonfinite", "deep"])
def test_strict_bounded_raw_boundary(raw, code):
    with pytest.raises(ValueError, match=code):
        ResearchSelection.from_bytes(raw, request())


def test_dto_copy_cannot_bypass_wire_validation():
    selection = CampaignResearchSelection.model_validate_json(json.dumps(document()))
    forged = selection.model_copy(update={"questions": (None,)})
    with pytest.raises(ValueError, match="invalid_campaign_context_selection"):
        ResearchSelection.bind(forged, request())
