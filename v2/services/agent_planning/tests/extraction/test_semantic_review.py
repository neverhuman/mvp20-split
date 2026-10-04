"""Independent review labels test scoring; native boundaries never claim entailment."""

import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest

from .semantic_boundary import inspect
from .semantic_review import CorpusCase, ReviewedResponse, canonical, digest, report

ROOT = Path(__file__).parent
MANIFEST = json.loads((ROOT / "corpus/manifest.json").read_bytes())
CASES = {row["case_id"]: CorpusCase.load(ROOT / "corpus", row) for row in MANIFEST["cases"]}
RECORDS = json.loads((ROOT / "semantic_fixtures/responses.json").read_bytes())


def reviewed(record):
    return ReviewedResponse.bind(CASES[record["case_id"]], record)


def test_frozen_response_set_pins_all_three_variants_without_changing_source_oracles():
    manifest = json.loads((ROOT / "semantic_fixtures/manifest.json").read_bytes())
    assert manifest["sha256"] == digest((ROOT / "semantic_fixtures" / manifest["response_file"]).read_bytes())
    assert manifest["corpus_sha256"] == digest((ROOT / "corpus/manifest.json").read_bytes())
    assert manifest["responses"] == len(RECORDS) == 54 and manifest["cases"] == len(CASES) == 18
    assert len({record["response_id"] for record in RECORDS}) == 54
    for case in CASES:
        assert {record["response_id"] for record in RECORDS if record["case_id"] == case} == {
            case + "-" + variant for variant in ("faithful", "incorrect", "abstained")}


@pytest.mark.parametrize("record", RECORDS, ids=[row["response_id"] for row in RECORDS])
def test_reviewed_response_runs_native_boundaries_without_semantic_authority(record):
    response = reviewed(record)
    result = inspect(response)
    packet = result["packet"]
    assert packet["source_data"][0]["text"].encode() == response.case.source
    assert "review" not in packet and "oracle" not in packet and "expected_meaning" not in canonical(packet).decode()
    assert response.case.source.decode() not in packet["trusted_instructions"]
    score = response.score().document()
    if response.response_id.endswith("faithful"):
        assert score["precision"] == score["recall"] == 1 and score["forbidden"] == 0
        assert result["status"] == "proposed"
        expected_quote = "no_quoted_candidates" if response.case.category in {"alias_collision", "retraction"} else "verified_geometry_only"
        assert result["quotation"] == expected_quote
    elif response.response_id.endswith("incorrect"):
        assert score["precision"] == score["recall"] == 0 and score["forbidden"] == 1
        # Correct citation bytes are compatible with a false scientific claim.
        assert result["status"] == "proposed" and result["quotation"] == "verified_geometry_only"
    else:
        assert score["precision"] is None and score["recall"] == 0 and score["abstained"] == 1
        assert result["status"] == "abstained"


def test_split_category_reports_do_not_hide_deliberate_bad_and_abstained_responses():
    result = report(tuple(CASES.values()), tuple(map(reviewed, RECORDS)))
    assert result["authority"] == "reviewed_synthetic_fixture_only"
    assert len(result["groups"]) == 18
    for group in result["groups"].values():
        assert group["responses"] == 3 and group["cases"] == 1
        assert group["abstained"] == 1 and group["provider_failed"] == 0 and group["forbidden"] == 1
        assert group["false_positive"] == 1 and group["false_negative"] == 2 * group["true_positive"]


@pytest.mark.parametrize("field", ["source_sha256", "oracle_sha256", "output_sha256"])
def test_altered_review_bindings_fail_closed(field):
    row = copy.deepcopy(RECORDS[0])
    row[field] = "f" * 64
    with pytest.raises(ValueError, match="binding"):
        reviewed(row)


@pytest.mark.parametrize("fault,code", [("unknown", "review_unknown_meaning"), ("unreviewed", "review_incomplete_output"),
    ("duplicate_path", "review_claim_identity"), ("missing_path", "review_output_path"), ("context", "review_index"),
    ("forbidden", "review_index"), ("authority", "review_authority")])
def test_incomplete_or_invalid_reviews_cannot_inflate_scores(fault, code):
    row = copy.deepcopy(RECORDS[0])
    if fault == "unknown": row["review"]["claims"][0]["meaning"] = 100
    if fault == "unreviewed": row["review"]["claims"] = []
    if fault == "duplicate_path": row["review"]["claims"] *= 2
    if fault == "missing_path": row["review"]["claims"][0]["path"] = "/assertions/99"
    if fault == "context": row["review"]["context_present"] = [0, 0]
    if fault == "forbidden": row["review"]["forbidden"] = [99]
    if fault == "authority": row["review"]["reviewer"] = "model_self_acceptance"
    with pytest.raises(ValueError, match=code): reviewed(row)


def test_duplicate_meaning_matches_count_as_false_positives_and_omissions_reduce_recall():
    row = copy.deepcopy(next(row for row in RECORDS if row["response_id"] == "held-negation-faithful"))
    row["review"]["claims"][1]["meaning"] = 0
    score = reviewed(row).score().document()
    assert (score["true_positive"], score["false_positive"], score["false_negative"]) == (1, 1, 1)
    assert score["precision"] == score["recall"] == 0.5


def test_report_requires_each_selected_case_and_unique_response_identity():
    rows = tuple(map(reviewed, RECORDS))
    with pytest.raises(ValueError, match="evaluation_missing_review"):
        report(tuple(CASES.values()), tuple(row for row in rows if row.case.case_id != "held-negation"))
    with pytest.raises(ValueError, match="evaluation_duplicate_identity"):
        report(tuple(CASES.values()), (*rows, rows[0]))
    with pytest.raises(ValueError, match="evaluation_empty"):
        report((), ())


def test_fabricated_quote_is_not_repaired_by_a_favorable_semantic_review():
    row = copy.deepcopy(RECORDS[0])
    row["output"]["assertions"][0]["attribution"]["quotations"][0]["text"] = "Invented exact quotation"
    row["output_sha256"] = digest(canonical(row["output"]))
    response = reviewed(row)
    assert response.score().true_positive == 1
    assert inspect(response)["quotation"] == "invalid"


def test_unknown_method_stays_missing_and_opinion_stays_inferred():
    response = reviewed(next(row for row in RECORDS if row["response_id"] == "held-opinion-faithful"))
    result = inspect(response)
    fields = {row["target_path"]: row for row in result["trace"]["fields"]}
    assert fields["/answers/0"]["origin"] == "model_inferred"
    assert fields["/answers/0/validation_method"]["origin"] == "missing"
    assert fields["/evidence_needs/0/method"]["origin"] == "missing"


@pytest.mark.parametrize("fault", ["tool_action", "acceptance_authority", "network_descriptor"])
def test_hostile_source_cannot_expand_the_closed_output_profile(fault):
    row = copy.deepcopy(next(row for row in RECORDS if row["response_id"] == "held-hostile-faithful"))
    if fault == "tool_action": row["output"]["action"] = "execute_tool"
    if fault == "acceptance_authority": row["output"]["authority"] = "accepted"
    if fault == "network_descriptor": row["output"]["tool"] = {"endpoint": "https://source-selected.invalid"}
    row["output_sha256"] = digest(canonical(row["output"]))
    result = inspect(reviewed(row))
    assert result["status"] in {"invalid", "policy_rejected"}
    assert result["quotation"] == "not_proposed"
    assert result["trace"]["outcome"]["candidate_sha256"] is None


def test_provider_failure_is_not_abstention_or_a_disappearing_case():
    row = copy.deepcopy(RECORDS[0])
    row["output"] = {"provider_error": "unavailable"}
    row["output_sha256"] = digest(canonical(row["output"]))
    row["review"].update(claims=[], context_present=[], forbidden=[], disposition="provider_failed")
    score = reviewed(row).score().document()
    assert score["provider_failed"] == 1 and score["abstained"] == 0
    assert score["precision"] is None and score["recall"] == 0 and score["false_negative"] == 1


def test_partial_response_keeps_omissions_in_the_denominator():
    row = copy.deepcopy(next(row for row in RECORDS if row["response_id"] == "held-negation-faithful"))
    row["output"]["diagnostics"] = []
    row["output_sha256"] = digest(canonical(row["output"]))
    row["review"]["claims"] = row["review"]["claims"][:1]
    row["review"]["context_present"] = [0]
    score = reviewed(row).score().document()
    assert score["precision"] == 1 and score["recall"] == 0.5
    assert score["context_present"] == 1 and score["context_total"] == 2


def test_unreviewed_edit_cannot_hide_behind_reviewed_assertions():
    row = copy.deepcopy(RECORDS[0])
    row["output"]["edits"] = [{"operation": "retract_assertion", "local_id": "unreviewed-edit"}]
    row["output_sha256"] = digest(canonical(row["output"]))
    with pytest.raises(ValueError, match="review_incomplete_output"):
        reviewed(row)


@pytest.mark.parametrize("fault,code", [("source", "corpus_digest"), ("oracle", "corpus_digest"),
    ("identity", "corpus_binding"), ("split", "corpus_split")])
def test_corpus_tampering_and_unknown_splits_fail_before_scoring(tmp_path, fault, code):
    row = copy.deepcopy(MANIFEST["cases"][0])
    for kind in ("source", "oracle"):
        raw = (ROOT / "corpus" / row[kind]).read_bytes()
        row[kind] = kind + ".json"
        (tmp_path / row[kind]).write_bytes(raw + b" " if kind == fault else raw)
    if fault == "identity": row["case_id"] = "different-case"
    if fault == "split": row["split"] = "tuned-held-out"
    with pytest.raises(ValueError, match=code):
        CorpusCase.load(tmp_path, row)


def test_response_cannot_be_moved_between_splits_after_review():
    rows = list(map(reviewed, RECORDS))
    rows[0] = replace(rows[0], case=replace(rows[0].case, split="held_out"))
    with pytest.raises(ValueError, match="evaluation_case_binding"):
        report(tuple(CASES.values()), rows)


@pytest.mark.parametrize("fault,code", [("label", "review_disposition"), ("hidden_claims", "review_empty_disposition"),
    ("false_abstention", "review_abstention_binding"), ("path", "review_output_path"), ("limit", "review_claim_limit")])
def test_review_cannot_relabel_claims_as_abstention_or_hide_malformed_annotations(fault, code):
    row = copy.deepcopy(RECORDS[0])
    if fault == "label": row["review"]["disposition"] = "accepted"
    if fault == "hidden_claims": row["review"]["disposition"] = "abstained"
    if fault == "false_abstention":
        row = copy.deepcopy(RECORDS[2])
        row["output"]["action"] = "propose_knowledge_change"
        row["output_sha256"] = digest(canonical(row["output"]))
    if fault == "path": row["review"]["claims"][0]["path"] = "not-a-path"
    if fault == "limit": row["review"]["claims"] *= 129
    with pytest.raises(ValueError, match=code):
        reviewed(row)
