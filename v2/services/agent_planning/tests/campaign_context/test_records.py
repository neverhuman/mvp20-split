import copy
import hashlib
import json
from pathlib import Path

import pytest
from amphora_agent_planning.campaign_context import (
    ResearchContext,
    ResearchGap,
    ResearchIdentity,
    ResearchReadSet,
    ResearchSelection,
)
from amphora_agent_planning.context import RequestSnapshot
from amphora_contracts_core import Scope
from amphora_contracts_research import (
    EvidenceAssessmentStatus,
    EvidenceNeed,
    ResearchQuestion,
)

FIXTURES = Path(__file__).parent / "fixtures"
MODELS = {"question": ResearchQuestion, "need": EvidenceNeed, "assessment": EvidenceAssessmentStatus}


def values():
    return json.loads((FIXTURES / "records.json").read_bytes())


def wire(kind, value):
    return MODELS[kind].model_validate_json(json.dumps(value))


def selected(records=None, selection=None):
    records = values() if records is None else records
    value = json.loads((FIXTURES / "selection.json").read_bytes()) if selection is None else selection
    if value["assessments"]:
        value["assessments"][0]["status_sha256"] = hashlib.sha256(json.dumps(
            records["assessment"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    request = RequestSnapshot.from_bytes((FIXTURES / "request.json").read_bytes(), actor_id="fixture",
                                        scope=Scope(tenant_id="planning-fixture", project_id="context"))
    return ResearchSelection.from_bytes(json.dumps(value).encode(), request)


def context(records=None, selection=None, omitted=(), unavailable=()):
    records = values() if records is None else records
    return ResearchContext.bind(selected(records) if selection is None else selection,
        questions=() if "question" in omitted else (wire("question", records["question"]),),
        needs=() if "need" in omitted else (wire("need", records["need"]),),
        assessments=() if "assessment" in omitted else (wire("assessment", records["assessment"]),),
        unavailable=unavailable)


def test_contradicted_science_is_retained_as_immutable_selected_metadata():
    data = values()
    projection = context(data)
    assert projection.selection.document().assessments[0].status_sha256 == json.loads(
        (FIXTURES / "records-identity.json").read_bytes())["assessment_status_sha256"]
    assert not projection.findings and not projection.gaps
    packet = json.loads(projection.canonical)
    assert packet["authority"] == "selected_metadata_only"
    status = packet["records"][2]["record"]["outcome"]["assessment"]
    assert status["disposition"] == "contradicted" and not status["sufficient"] and not status["scientifically_established"]
    assert context(copy.deepcopy(data)).sha256 == projection.sha256
    data["question"]["criteria"].clear()
    packet["records"].clear()
    assert len(projection.records[0].document().criteria) == 1
    assert len(json.loads(projection.canonical)["records"]) == 3


@pytest.mark.parametrize("posture", ["supported", "contradicted", "unknown"])
def test_owner_posture_is_never_a_global_quality_filter(posture):
    data = values()
    data["assessment"]["outcome"]["assessment"]["disposition"] = posture
    projection = context(data)
    assert projection.records[-1].document().outcome.assessment.disposition == posture
    assert not projection.findings


def test_missing_and_denied_inputs_preserve_other_records_and_dependency_findings():
    empty = ResearchContext.bind(selected())
    assert len(empty.gaps) == 3 and {item.reason for item in empty.gaps} == {"not_provided"}
    identity = ResearchIdentity.bind("question", wire("question", values()["question"]).reference)
    partial = context(omitted=("question",), unavailable=(ResearchGap(identity, "denied"),))
    assert len(partial.records) == 2 and partial.gaps == (ResearchGap(identity, "denied"),)
    assert {item.reason for item in partial.findings} == {"question_unavailable"}
    changes = partial.read_set().changes(context().read_set())
    assert [(change.identity.kind, change.reason) for change in changes] == [("question", "changed")]


@pytest.mark.parametrize("state", ["pending", "failed"])
def test_incomplete_assessment_becomes_explicit_gap_not_a_pinned_completed_record(state):
    data = values()
    data["assessment"]["outcome"] = {"status": state, **({"code": "fixture_unavailable"} if state == "failed" else {})}
    projection = context(data, selected())
    assert len(projection.records) == 2 and projection.gaps[0].reason == state
    assert projection.gaps[0].identity.kind == "assessment"


@pytest.mark.parametrize("kind", ["question", "need", "assessment"])
def test_duplicate_and_unselected_owner_records_fail(kind):
    record = wire(kind, values()[kind])
    argument = {"question": "questions", "need": "needs", "assessment": "assessments"}[kind]
    with pytest.raises(ValueError, match="campaign_record_duplicate"):
        ResearchContext.bind(selected(), **{argument: (record, record)})
    data = values()[kind]
    if kind == "assessment":
        data["request"]["assessment_id"] = "other"
    else:
        data["reference"][kind + "_id"] = "other"
    with pytest.raises(ValueError, match="campaign_record_not_selected"):
        ResearchContext.bind(selected(), **{argument: (wire(kind, data),)})


def test_expected_status_hash_binds_all_owner_fields():
    data = values()
    data["assessment"]["outcome"]["assessment"]["sufficient"] = True
    with pytest.raises(ValueError, match="campaign_assessment_digest"):
        context(data, selected())


@pytest.mark.parametrize("variant,code", [
    ("question_scope", "campaign_record_scope"), ("need_scope", "campaign_record_scope"),
    ("subject_scope", "campaign_record_scope"), ("question_duplicate", "campaign_record_duplicate_criterion"),
    ("need_duplicate", "campaign_record_duplicate_criterion"), ("need_unknown", "campaign_record_unknown_criterion"),
    ("question_predecessor", "campaign_record_predecessor"), ("need_predecessor", "campaign_record_predecessor"),
    ("assessment_actor", "campaign_assessment_origin"), ("assessment_request", "campaign_assessment_origin"),
    ("assessment_duplicate", "campaign_assessment_duplicate_need"), ("assessment_criterion", "campaign_record_unknown_criterion"),
    ("assessment_gap", "campaign_assessment_gap_binding"), ("assessment_receipt", "campaign_assessment_receipt_binding"),
    ("assessment_review", "campaign_assessment_receipt_binding"), ("assessment_scope", "campaign_record_scope"),
])
def test_nested_owner_record_coherence(variant, code):
    data = values()
    q, n, a = data["question"], data["need"], data["assessment"]["outcome"]["assessment"]
    if variant == "question_scope":
        q["applicability"]["scope"]["project_id"] = "foreign"
    elif variant == "need_scope":
        n["required_context"]["scope"]["project_id"] = "foreign"
    elif variant == "subject_scope":
        a["subject"]["scope"]["project_id"] = "foreign"
    elif variant == "question_duplicate":
        q["criteria"].append(copy.deepcopy(q["criteria"][0]))
    elif variant == "need_duplicate":
        n["criterion_ids"].append(n["criterion_ids"][0])
    elif variant == "need_unknown":
        n["criterion_ids"] = ["invented"]
    elif variant == "question_predecessor":
        q["supersedes"] = copy.deepcopy(q["reference"])
    elif variant == "need_predecessor":
        n["supersedes"] = copy.deepcopy(n["reference"])
    elif variant == "assessment_actor":
        a["actor_id"] = "other"
    elif variant == "assessment_request":
        a["request"]["assessment_id"] = "other"
    elif variant == "assessment_duplicate":
        a["needs"].append(copy.deepcopy(a["needs"][0]))
    elif variant == "assessment_criterion":
        a["needs"][0]["criterion_id"] = "invented"
    elif variant == "assessment_gap":
        a["needs"][0]["gap"]["criterion_id"] = "other"
    elif variant == "assessment_receipt":
        a["needs"][0]["contradicting"][0]["sha256"] = "f" * 64
    elif variant == "assessment_review":
        a["reviews"][0]["receipt"]["sha256"] = "f" * 64
    else:
        a["needs"][0]["need"]["scope"]["project_id"] = "foreign"
    with pytest.raises(ValueError, match=code):
        context(data)


def test_unselected_or_missing_need_is_a_gap_in_context_not_erased_evidence():
    projection = context(omitted=("need",))
    assert [item.reason for item in projection.findings] == ["need_unavailable"]
    choice = selected().document().model_dump(mode="json")
    choice["needs"] = []
    projection = context(selection=selected(selection=choice), omitted=("need",))
    assert [item.reason for item in projection.findings] == ["need_not_selected"]
    assert projection.records[-1].document().outcome.assessment.disposition == "contradicted"
    choice["questions"], choice["assessments"] = [], []
    choice["needs"] = [values()["need"]["reference"]]
    projection = context(selection=selected(selection=choice), omitted=("question", "assessment"))
    assert [item.reason for item in projection.findings] == ["question_not_selected"]


def test_read_set_detects_relevant_changes_and_ignores_new_unrelated_records():
    original = context()
    data = values()
    data["question"]["criteria"][0]["description"] = "Changed criteria require a new proposal review."
    changed = context(data)
    assert [(item.identity.kind, item.reason) for item in original.read_set().changes(changed.read_set())] == [("question", "changed")]
    assert len(original.read_set().changes(ResearchReadSet(()))) == 3
    choice = selected().document().model_dump(mode="json")
    other = copy.deepcopy(data["question"])
    other["reference"]["question_id"] = "unrelated"
    choice["questions"].append(other["reference"])
    source = values()
    expanded = ResearchContext.bind(selected(selection=choice),
        questions=(wire("question", other), wire("question", source["question"])),
        needs=(wire("need", source["need"]),), assessments=(wire("assessment", source["assessment"]),))
    assert not original.read_set().changes(expanded.read_set())
    assert original.selection.sha256 != expanded.selection.sha256


def test_valid_historical_predecessors_do_not_select_latest_implicitly():
    choice = selected().document().model_dump(mode="json")
    data = values()
    choice["assessments"] = []
    for kind, field in (("question", "questions"), ("need", "needs")):
        data[kind]["supersedes"] = copy.deepcopy(data[kind]["reference"])
        data[kind]["reference"]["revision"] = 2
        choice[field] = [data[kind]["reference"]]
    data["need"]["question"] = data["question"]["reference"]
    result = context(data, selected(selection=choice), omitted=("assessment",))
    assert not result.findings and len(result.records) == 2


def test_gap_identity_collisions_and_limits_fail():
    identity = ResearchIdentity.bind("question", wire("question", values()["question"]).reference)
    gap = ResearchGap(identity, "denied")
    with pytest.raises(ValueError, match="campaign_record_gap_binding"):
        context(unavailable=(gap,))
    with pytest.raises(ValueError, match="campaign_record_gap_binding"):
        ResearchContext.bind(selected(), unavailable=(gap, gap))
    with pytest.raises(ValueError, match="campaign_record_gap_reason"):
        ResearchGap(identity, "scientifically_accepted")
    with pytest.raises(ValueError, match="campaign_record_gap_limit"):
        ResearchContext.bind(selected(), unavailable=[gap])
    with pytest.raises(ValueError, match="campaign_record_count"):
        ResearchContext.bind(selected(), questions=[])
    with pytest.raises(ValueError, match="campaign_read_set_duplicate"):
        ResearchReadSet(context().read_set().entries * 2)
    with pytest.raises(ValueError, match="campaign_read_set_limit"):
        ResearchReadSet(context().read_set().entries * 54)


def test_record_and_aggregate_byte_limits_do_not_silently_truncate():
    question = wire("question", values()["question"])
    oversized = question.model_copy(update={"objective": "x" * 1048576})
    with pytest.raises(ValueError, match="campaign_record_size"):
        ResearchContext.bind(selected(), questions=(oversized,))
    choice = selected().document().model_dump(mode="json")
    choice["questions"], choice["needs"], choice["assessments"] = [], [], []
    records = []
    for i in range(64):
        record = values()["question"]
        record["reference"]["question_id"] = f"question-{i}"
        record["criteria"] = [{"criterion_id": f"criterion-{j}", "description": "x" * 2048} for j in range(32)]
        choice["questions"].append(record["reference"])
        records.append(wire("question", record))
    with pytest.raises(ValueError, match="campaign_context_record_bytes"):
        ResearchContext.bind(selected(selection=choice), questions=tuple(records))
